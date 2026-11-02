from __future__ import annotations

import sys
import traceback
from pathlib import Path

from app.tech_logger import create_technical_logger


PROJECT_DIR = Path(__file__).resolve().parent


def install_exception_hook(logger) -> None:
    """Логирует необработанные исключения верхнего уровня в технический лог."""

    def _hook(exc_type, exc_value, exc_traceback) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        traceback_text = "".join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        ).strip()
        logger.error(f"Необработанное исключение верхнего уровня\n{traceback_text}")
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = _hook


def preload_ml_dependencies(logger) -> None:
    """
    Предварительно загружает ML-зависимости до импорта PyQt5.

    Это нужно из-за реального конфликта порядка загрузки DLL на Windows:
    если PyQt5 загрузится раньше torch, импорт ultralytics может падать с WinError 1114.
    """

    from app.video_analyzer import preload_inference_dependencies

    preload_inference_dependencies()
    logger.info("ML-зависимости предварительно загружены")


def main() -> int:
    """Точка входа в приложение."""

    logger = create_technical_logger(PROJECT_DIR)
    logger.info("Программа запущена")
    install_exception_hook(logger)

    try:
        preload_ml_dependencies(logger)
        from PyQt5.QtWidgets import QApplication
        from app.main_window import MainWindow
    except Exception as exc:
        logger.exception(
            "Не удалось подготовить зависимости приложения.",
            exc,
        )
        print(
            "Ошибка запуска приложения.\n"
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    try:
        app = QApplication(sys.argv)
        app.setApplicationName("AI for safe driving")
        window = MainWindow(logger=logger, project_dir=PROJECT_DIR)
        window.show()
        return app.exec_()
    except Exception as exc:
        logger.exception("Критическая ошибка при запуске приложения", exc)
        print(f"Критическая ошибка запуска: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
