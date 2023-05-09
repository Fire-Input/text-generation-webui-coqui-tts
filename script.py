from TTS.api import TTS
import re
from pathlib import Path
import gradio as gr

from modules import chat, shared
from modules.html_generator import chat_html_wrapper

params = {
    'activate': True,
    'selected_speaker': 'None',
    'language': 'en',
    'model_name': 'tts_models/en/vctk/vits',
    'gpu': False,
    'show_text': True,
    'autoplay': True,
}

speakers = None
wav_idx = 0

# For tts_models/en/vctk/vits only.
# voices_by_gender = ["p225", "p227", "p237", "p240", "p243", "p244", "p245", "p246", "p247", "p248", "p249", "p250", "p259", "p260", "p261", "p263", "p268", "p270", "p271", "p273", "p274", "p275", "p276", "p277", "p278", "p280", "p283", "p284", "p288", "p293", "p294", "p295", "p297", "p300", "p303", "p304", "p305", "p306", "p308", "p310", "p311", "p314", "p316", "p323", "p329", "p334", "p335", "p336", "p339", "p341", "p343", "p345", "p347", "p360", "p361", "p363", "p364"]

available_models = TTS.list_models()


def refresh_speakers():
    global params
    speaker_names = TTS(params['model_name'], progress_bar=False).speakers
    if speaker_names is not None:
        return speaker_names
    else:
        return None


def refresh_speakers_dd():
    all_voices = refresh_speakers()
    if all_voices is not None:
        return gr.Dropdown.update(value=all_voices[0], choices=all_voices)
    else:
        return gr.Dropdown.update(value='None', choices=['None'])


def remove_tts_from_history(name1, name2, mode, style):
    for i, entry in enumerate(shared.history['internal']):
        shared.history['visible'][i] = [shared.history['visible'][i][0], entry[1]]

    return chat_html_wrapper(shared.history['visible'], name1, name2, mode, style)


def toggle_text_in_history(name1, name2, mode, style):
    for i, entry in enumerate(shared.history['visible']):
        visible_reply = entry[1]
        if visible_reply.startswith('<audio'):
            if params['show_text']:
                reply = shared.history['internal'][i][1]
                shared.history['visible'][i] = [shared.history['visible'][i][0], f"{visible_reply.split('</audio>')[0]}</audio>\n\n{reply}"]
            else:
                shared.history['visible'][i] = [shared.history['visible'][i][0], f"{visible_reply.split('</audio>')[0]}</audio>"]

    return chat_html_wrapper(shared.history['visible'], name1, name2, mode, style)


def state_modifier(state):
    state['stream'] = False
    return state


def remove_surrounded_chars(string):
    # this expression matches to 'as few symbols as possible (0 upwards) between any asterisks' OR
    # 'as few symbols as possible (0 upwards) between an asterisk and the end of the string'
    return re.sub('\*[^\*]*?(\*|$)', '', string)


def input_modifier(string):
    """
    This function is applied to your text inputs before
    they are fed into the model.
    """
    # Remove autoplay from the last reply
    if shared.is_chat() and len(shared.history['internal']) > 0:
        shared.history['visible'][-1] = [
            shared.history['visible'][-1][0],
            shared.history['visible'][-1][1].replace('controls autoplay>', 'controls>')
        ]

    if params['activate']:
        shared.processing_message = "*Is recording a voice message...*"

    return string


def output_modifier(string):
    """
    This function is applied to the model outputs.
    """

    global params, wav_idx

    if not params['activate']:
        return string

    original_string = string
    string = remove_surrounded_chars(string)
    string = string.replace('"', '')
    string = string.replace('“', '')
    string = string.replace('\n', ' ')
    string = string.strip()
    if string == '':
        string = 'empty reply, try regenerating'

    output_file = Path(f'extensions/coqui_tts/outputs/{wav_idx:06d}.wav')
    print(f'Outputting audio to {str(output_file)}')
    try:
        tts = TTS(model_name=params['model_name'], progress_bar=False, gpu=params['gpu'])
        if not tts.is_multi_speaker:
            params['selected_speaker'] = None
        if tts.is_multi_lingual:
            tts.tts_to_file(text=string, file_path=str(output_file), speaker=params['selected_speaker'], language=params['language'])
        else:
            tts.tts_to_file(text=string, file_path=str(output_file), speaker=params['selected_speaker'])
        autoplay = 'autoplay' if params['autoplay'] else ''
        string = f'<audio src="file/{output_file.as_posix()}" controls {autoplay}></audio>'
        wav_idx += 1
    except FileNotFoundError as err:
        string = f"🤖 Coqui TTS FileNotFoundError: {err}\n\n"
    except ValueError as err:
        string = f"🤖 Coqui TTS ValueError: {err}\n\n"

    if params['show_text']:
        string += f'\n\n{original_string}'

    shared.processing_message = "*Is typing...*"
    return string


def ui():
    global speakers
    if not speakers:
        speakers = refresh_speakers()
        params['selected_speaker'] = speakers[0]

    # Gradio elements
    with gr.Row():
        activate = gr.Checkbox(value=params['activate'], label='Activate TTS')
        autoplay = gr.Checkbox(value=params['autoplay'], label='Play TTS automatically')
        show_text = gr.Checkbox(value=params['show_text'], label='Show message text under audio player')

    with gr.Row():
        model = gr.Dropdown(value=params['model_name'], choices=available_models, label='TTS Model')

    with gr.Row():
        speaker = gr.Dropdown(value=params['selected_speaker'], choices=speakers, label='TTS Speaker')
        refresh = gr.Button(value='Refresh')

    with gr.Row():
        convert = gr.Button('Permanently replace audios with the message texts')
        convert_cancel = gr.Button('Cancel', visible=False)
        convert_confirm = gr.Button('Confirm (cannot be undone)', variant="stop", visible=False)

    # Convert history with confirmation
    convert_arr = [convert_confirm, convert, convert_cancel]
    convert.click(
        lambda: [gr.update(visible=True), gr.update(visible=False),
                 gr.update(visible=True)], None, convert_arr
    )
    convert_confirm.click(
        lambda: [gr.update(visible=False), gr.update(visible=True),
                 gr.update(visible=False)], None, convert_arr
    )
    convert_confirm.click(
        remove_tts_from_history, [shared.gradio[k] for k in ['name1', 'name2', 'mode', 'chat_style']], shared.gradio['display']
    )
    convert_confirm.click(chat.save_history, shared.gradio['mode'], [], show_progress=False)
    convert_cancel.click(
        lambda: [gr.update(visible=False), gr.update(visible=True),
                 gr.update(visible=False)], None, convert_arr
    )

    # Event functions to update the parameters in the backend
    activate.change(lambda x: params.update({'activate': x}), activate, None)
    model.change(lambda x: params.update({'model_name': x}), model, None)
    speaker.change(lambda x: params.update({'selected_speaker': x}), speaker, None)
    refresh.click(refresh_speakers_dd, [], speaker)
    # Toggle message text in history
    show_text.change(lambda x: params.update({"show_text": x}), show_text, None)
    show_text.change(
        toggle_text_in_history, [shared.gradio[k] for k in ['name1', 'name2', 'mode', 'chat_style']], shared.gradio['display']
    )
    show_text.change(chat.save_history, shared.gradio['mode'], [], show_progress=False)
    # Event functions to update the parameters in the backend
    autoplay.change(lambda x: params.update({"autoplay": x}), autoplay, None)
