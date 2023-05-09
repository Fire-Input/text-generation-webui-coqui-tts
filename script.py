from TTS.api import TTS
from pathlib import Path
import gradio as gr
import time
import traceback

from modules import chat, shared, tts_preprocessor
from modules.html_generator import chat_html_wrapper


params = {
    'activate': True,
    'selected_speaker': None,
    'language': None,
    'model_name': 'tts_models/en/vctk/vits',
    'gpu': False,
    'show_text': True,
    'autoplay': True,
    'voice_clone_reference_path': None,
    'show_processed_text': False,
}

current_params = params.copy()
speakers = []
languages = []

# For tts_models/en/vctk/vits only.
# voices_by_gender = ["p225", "p227", "p237", "p240", "p243", "p244", "p245", "p246", "p247", "p248", "p249", "p250", "p259", "p260", "p261", "p263", "p268", "p270", "p271", "p273", "p274", "p275", "p276", "p277", "p278", "p280", "p283", "p284", "p288", "p293", "p294", "p295", "p297", "p300", "p303", "p304", "p305", "p306", "p308", "p310", "p311", "p314", "p316", "p323", "p329", "p334", "p335", "p336", "p339", "p341", "p343", "p345", "p347", "p360", "p361", "p363", "p364"]

models = TTS.list_models()


def load_model():
    # Init TTS
    global speakers, params
    tts = TTS(params['model_name'], gpu=params['gpu'])
    if tts is not None and tts.synthesizer is not None and tts.synthesizer.tts_config is not None and hasattr(
            tts.synthesizer.tts_config, 'num_chars'):
        tts.synthesizer.tts_config.num_chars = 250

    speakers = tts.speakers if tts.speakers is not None else []
    temp_speaker = params['selected_speaker'] if params['selected_speaker'] in speakers else speakers[0] if len(speakers) > 0 else None

    languages = tts.languages if tts.languages is not None else []
    temp_language = params['language'] if params['language'] in languages else languages[0] if len(
        languages) > 0 else None

    return tts, temp_speaker, temp_language


model, speaker, language = load_model()


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

    global model, speaker, language, current_params

    for i in params:
        if params[i] != current_params[i]:
            model, speaker, language = load_model()
            current_params = params.copy()
            break

    if not current_params['activate']:
        return string

    original_string = string
    # we don't need to handle numbers. The text normalizer in coqui does it better
    string = tts_preprocessor.replace_invalid_chars(string)
    # string = tts_preprocessor.replace_abbreviations(string)
    string = tts_preprocessor.clean_whitespace(string)
    processed_string = string
    if string == '':
        string = 'empty reply, try regenerating'
    else:
        output_file = Path(f'extensions/coqui_tts/outputs/{shared.character}_{int(time.time())}.wav')
        print(f'Outputting audio to {str(output_file)}')

        try:
            if params['voice_clone_reference_path'] is not None:
                model.tts_with_vc_to_file(text=string, language=params['language'], speaker_wav=params['voice_clone_reference_path'], file_path=str(output_file))
            else:
                model.tts_to_file(text=string, file_path=str(output_file), speaker=params['selected_speaker'], language=params['language'])
            autoplay = 'autoplay' if params['autoplay'] else ''
            string = f'<audio src="file/{output_file.as_posix()}" controls {autoplay}></audio>'
        except FileNotFoundError as err:
            string = f"🤖 Coqui TTS FileNotFoundError: {err}\n\n"
        except ValueError as err:
            string = f"🤖 Coqui TTS ValueError: {err}\n\n"

        if params['show_text'] and params['show_processed_text']:
            string += f'\n\n{original_string}\n\nProcessed:\n{processed_string}'
        elif params['show_text']:
            string += f'\n\n{original_string}'

    shared.processing_message = "*Is typing...*"
    return string


def setup():
    global model, speaker, language
    model, speaker, language = load_model()


def bot_prefix_modifier(string):
    """
    This function is only applied in chat mode. It modifies
    the prefix text for the Bot and can be used to bias its
    behavior.
    """

    return string


def ui():
    # Gradio elements
    with gr.Accordion("Coqui AI TTS"):
        with gr.Row():
            activate = gr.Checkbox(value=params['activate'], label='Activate TTS')
            autoplay = gr.Checkbox(value=params['autoplay'], label='Play TTS automatically')
            gpu = gr.Checkbox(value=params['gpu'], label='Use GPU')

        show_text = gr.Checkbox(value=params['show_text'], label='Show message text under audio player')
        show_processed_text = gr.Checkbox(value=params['show_processed_text'], label='Show processed text under audio player')
        model_dropdown = gr.Dropdown(value=models[models.index(params['model_name'])] if params['model_name'] in models else None, choices=models, type='index', label='TTS Model')
        speaker_dropdown = gr.Dropdown(value=params['selected_speaker'], choices=model.speakers if model.speakers is not None else [], label='TTS Speaker')
        language_dropdown = gr.Dropdown(value=params['language'], choices=model.languages if model.languages is not None else [], label='Language')
        vc_textbox = gr.Textbox(value=params['voice_clone_reference_path'], label='Voice Clone Speaker Path')

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
    model_dropdown.change(lambda x: update_model(x), model_dropdown, [speaker_dropdown, language_dropdown])
    speaker_dropdown.change(lambda x: params.update({"selected_speaker": x}), speaker_dropdown, None)
    language_dropdown.change(lambda x: params.update({"language": x}), language_dropdown, None)
    vc_textbox.change(lambda x: params.update({"voice_clone_reference_path": x}), vc_textbox, None)
    gpu.change(lambda x: params.update({"gpu": x}), gpu, None)

    # Toggle message text in history
    show_text.change(lambda x: params.update({"show_text": x}), show_text, None)
    show_text.change(
        toggle_text_in_history, [shared.gradio[k] for k in ['name1', 'name2', 'mode', 'chat_style']], shared.gradio['display']
    )
    show_text.change(chat.save_history, shared.gradio['mode'], [], show_progress=False)
    show_processed_text.change(lambda x: params.update({"show_processed_text": x}), show_processed_text, None)
    # Event functions to update the parameters in the backend
    autoplay.change(lambda x: params.update({"autoplay": x}), autoplay, None)


def update_model(x):
    try:
        model_name = TTS.list_models()[x]
    except ValueError:
        model_name = None
    params.update({"model_name": model_name})
    global model, speaker, language, speakers, languages
    try:
        model, speaker, language = load_model()
    except:
        print(traceback.format_exc())
    return [gr.update(value=speaker, choices=speakers), gr.update(value=language, choices=languages)]
