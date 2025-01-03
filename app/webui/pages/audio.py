import logging
import re

import gradio as gr
import numpy as np

from app.configs.settings import get_email_settings
from app.services import AudioRecognizer, AudioUploader, Email, EmailSender

from .interfaces import Page

logger = logging.getLogger("stdout")
email_settings = get_email_settings()
logger.debug(f"Email settings: {email_settings}")


class AudioPage(Page):
    re_email = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    email_message = """Здравствуйте!
    \nВы получили аудио запрос на расшифровку в моей группе.
    \nЕсли вы получили это сообщение по ошибке, то сообщите мне по email или в чате.
    """
    email_message_transcribe = """Здравствуйте!
    \nВаша расшифровка аудио запроса:
    \n%s
    \nЕсли вы получили это сообщение по ошибке, то сообщите мне по email или в чате.
    """

    def __init__(self):
        self.audo_recoginition = AudioRecognizer()
        self.audio_uploader = AudioUploader()
        self.email_sender = EmailSender(email_settings)
        self.theme = None

    @property
    def title(self) -> str:
        return "Загрузка аудио"

    # Test emails:
    # go@yandex.ru;print; urea@gmai l.com, so@ydex.ru;print; urea@gmail.com
    def __filter_emails(self, emails: str) -> tuple:
        return tuple(filter(self.re_email.findall, emails.split(";")))

    def _send_email(self, emails: tuple[str], text: str):
        gr.Info(f"Отправлено уведомление для {emails} пользователей")
        logger.info(f"Sending emails to {emails}")

        g_emails = (Email(email, text) for email in emails)
        self.email_sender.execute(g_emails)
        return emails

    def __do(self, audio: np.ndarray, raw_emails: str, checkbox_speed: bool):
        logger.debug(f"Audio: {audio}")
        if not audio:
            raise ValueError("Укажите аудио для загрузки.")

        logger.debug(f"Doing with {raw_emails}")
        emails = self.__filter_emails(raw_emails)
        if not emails:
            raise ValueError(
                "Пожалуйста, укажите хотя бы один email.\n Используйте ';' как разделитель для email'ов"
            )

        self._send_email(emails, self.email_message)
        text_audio = self._recoginition_audio(audio, checkbox_speed)
        if not text_audio:
            raise ValueError("Не удалось расшифровать аудио")
        # self._upload_file(audio, checkbox_speed)
        self._send_email(emails, self.email_message_transcribe % text_audio)

    def _recoginition_audio(self, audio: np.ndarray, speed: bool) -> str:
        logger.info(f"Speed: {speed}")
        gr.Info(f"Расшифровка {audio} файла")
        return self.audo_recoginition.execute(audio)

    def _upload_file(self, audio: np.ndarray, speed: bool):
        logger.info(f"Speed: {speed}")
        logger.info(f"Uploading {len(audio)} files")
        gr.Info(f"Загрузка {audio} файлов")
        # file_paths = [file.name for file in files]
        # return file_paths

    def get_app(self) -> gr.Blocks:
        with gr.Blocks(
            theme=self.theme,
            head="Prompts",
            title="Prompts",
            css="footer {visibility: hidden}",
        ) as app:
            gr.Markdown("# Upload audio")

            gr.Markdown("### Укажите email'ы для отправки расшифрованного аудио")
            with gr.Row(equal_height=True, variant="panel"):
                with gr.Column(scale=1):
                    text_emails = gr.Textbox(
                        lines=1,
                        interactive=True,
                        show_copy_button=True,
                        info="Используйте ';' как разделитель для email'ов",
                        label="Введитe cписок email'ов:",
                    )
            audio_input = gr.Audio(
                interactive=True,
                label="Выберите аудио для загрузки",
                type="numpy",
                waveform_options=gr.WaveformOptions(
                    waveform_color="#01C6FF",
                    waveform_progress_color="#0066B4",
                    # skip_length=2,
                    # show_controls=False,
                ),
            )
            with gr.Row(equal_height=True, variant="panel"):
                checbox_speed = gr.Checkbox(
                    label="Быстро", info="Если выбрано, то будет увеличена скорость загрузки аудио"
                )
                gr.Textbox(
                    lines=1,
                    interactive=False,
                    label="Время Загрузки:",
                    show_copy_button=True,
                    value="0:00:00.00",
                )
            start_button = gr.Button(
                "Отправить аудио",
                size="lg",
                variant="primary",
            )
            start_button.click(fn=self.__do, inputs=[audio_input, text_emails, checbox_speed])

            # audio_input.change(
            #     inputs=audio_input, outputs=text_output, fn=lambda x: f"Audio changed to {x}"
            # )

        return app
