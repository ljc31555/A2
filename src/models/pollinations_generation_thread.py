from PyQt5.QtCore import QThread, pyqtSignal
from src.models.pollinations_client import PollinationsClient
from src.utils.project_manager import ProjectManager
from src.utils.logger import logger # Corrected import

# logger is now directly usable

class PollinationsGenerationThread(QThread):
    generation_complete = pyqtSignal(str, object)  # image_path_or_error, metadata
    generation_failed = pyqtSignal(str)
    generation_progress = pyqtSignal(int, str) # progress, message

    def __init__(self, prompt: str, parameters: dict, project_manager: ProjectManager, current_project_name: str, parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.parameters = parameters if parameters is not None else {}
        self.project_manager = project_manager
        self.current_project_name = current_project_name
        self.pollinations_client = PollinationsClient()
        self._is_cancelled = False
        logger.debug(f"PollinationsGenerationThread initialized with prompt: '{self.prompt}', parameters: {self.parameters}")

    def run(self):
        try:
            if self._is_cancelled:
                self.generation_failed.emit("Generation cancelled by user.")
                return

            logger.info(f"Starting Pollinations generation for prompt: {self.prompt} with parameters: {self.parameters}")
            
            image_path_or_error = self.pollinations_client.generate_image(
                prompt=self.prompt,
                **self.parameters 
            )

            if self._is_cancelled:
                self.generation_failed.emit("Generation cancelled by user.")
                return

            if isinstance(image_path_or_error, str) and image_path_or_error.startswith("Error:"):
                logger.error(f"Pollinations generation failed: {image_path_or_error}")
                self.generation_failed.emit(image_path_or_error)
            else:
                metadata = {"prompt": self.prompt, "parameters": self.parameters, "source": "Pollinations"}
                image_path = image_path_or_error 

                if self.project_manager and self.current_project_name:
                    saved_path = self.project_manager.add_image_to_project(self.current_project_name, image_path, metadata)
                    if saved_path:
                        logger.info(f"Pollinations image generated and saved to project: {saved_path}")
                        self.generation_complete.emit(saved_path, metadata)
                    else:
                        logger.error("Failed to save Pollinations image to project.")
                        self.generation_failed.emit("Error: Failed to save image to project.")
                else:
                    logger.info(f"Pollinations image generated (no project context): {image_path}")
                    self.generation_complete.emit(image_path, metadata)
                    
        except Exception as e:
            logger.error(f"Exception in PollinationsGenerationThread: {e}", exc_info=True)
            self.generation_failed.emit(f"Error during Pollinations generation: {str(e)}")

    def cancel(self):
        self._is_cancelled = True
        if hasattr(self.pollinations_client, 'cancel_generation'):
            self.pollinations_client.cancel_generation()
        logger.info("Pollinations generation cancellation requested.")