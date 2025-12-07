from pathlib import Path
from shutil import copy as copy_file, make_archive as zip_directory
from time import sleep

from fastapi import BackgroundTasks

from app.logging.logger import generate_context_id, log


class TemporaryZip:
    """
    A temporarily-existing zip directory. Files can be aded to and
    zipped from the directory.
    """

    def __init__(self,
            temporary_directory: Path,
            background_tasks: BackgroundTasks,
            *,
            name: str | None = None,
        ) -> None:
        """
        Initialize a new temporary directory.

        Args:
            temporary_directory: Root directory where zips should be
                created.
            background_tasks: Task queue to add the delayed deletion to.
            name: Optional name of the zipped subdirectory. If omitted,
                a randomized name is generated.
        """

        self.tasks = background_tasks

        # Generate a random subfolder
        zip_dir = temporary_directory / 'zips'
        context_id = name or generate_context_id()
        self.dir = zip_dir / context_id
        self.dir.mkdir(exist_ok=True, parents=True)
        self.__files = 0


    def __bool__(self) -> bool:
        """
        Whether this zip folder has files or not.

        Returns:
            True if this zip has had files added to it, False otherwise.
        """

        return self.__files > 0


    def __delete_zip(self, directory: Path, file: Path) -> None:
        """
        Delete the given zip directory and files. A delay is utilized so
        that the browser is able to download the content before they are
        deleted.

        Args:
            directory: Directory containing zipped files to be deleted.
                The contents are deleted, then the directory itself.
            file: Zip file to delete directly.
        """

        # Wait a while to give the browser time to download the zips
        sleep(5)

        # Delete zipped file
        file.unlink(missing_ok=True)
        log.debug(f'Deleted "{file}"')

        # Delete zip directory contents
        for file in directory.glob('*'):
            file.unlink(missing_ok=True)
            log.debug(f'Deleted "{file}"')

        # Delete zip directory
        directory.rmdir()
        log.debug(f'Deleted {directory}')


    def add_file(self, file: Path, filename: str | None = None) -> None:
        """
        Add the given file to this directory for future zipping.

        Args:
            file: File to add to copy into this directory.
            filename: Filename to name `file` as. If not provided, then
                the original filename is used.
        """

        copy_file(file, self.dir / (filename or file.name))
        log.debug(f'Copied "{file}" into zip directory')
        self.__files += 1


    def zip(self) -> Path:
        """
        Zip this object's directory and then queue its deletion.

        Returns:
            Path to the created zip file.
        """

        zip_file = Path(zip_directory(str(self.dir), 'zip', self.dir))
        self.tasks.add_task(
            self.__delete_zip,
            directory=self.dir, file=zip_file,
        )

        return zip_file
