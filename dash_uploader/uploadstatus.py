from pathlib import Path
import os
import warnings


from typing import Union, Optional

try:
    from typing import Sequence
except ImportError:
    from collections.abc import Sequence

from typing_extensions import TypedDict


class UploadStatus(TypedDict):
    """
    The keywords of UploadStatus are:

    status.latest_file (pathlib.Path):
        The full file path to the file that has been latest uploaded
    status.uploaded_files (list of pathlib.Path):
        The list of full file paths to all of the uploaded files. (uploaded in this session)
    status.is_completed (bool):
        True if all the files have been uploaded
    status.n_uploaded (int):
        The number of files already uploaded in this session
    status.n_total (int):
        The number of files to be uploaded.
    status.uploaded_size_mb (float):
        Size of files uploaded in Megabytes
    status.total_size_mb (float):
        Total size of files to be uploaded in Megabytes
    status.upload_id (str or None):
        The upload id used in the upload process, if any.
    """

    uploaded_files: Sequence[str]
    latest_file: str
    n_uploaded: int
    n_total: int
    upload_id: Optional[str]
    is_completed: bool
    n_uploaded: int
    uploaded_size_mb: float
    total_size_mb: float
    progress: float


class UploadStatusLegacy:  # Deprecated, since it is not compatible with JSON serialization.
    """
    The attributes of UploadStatus are:

    status.latest_file (pathlib.Path):
        The full file path to the file that has been latest uploaded
    status.uploaded_files (list of pathlib.Path):
        The list of full file paths to all of the uploaded files. (uploaded in this session)
    status.is_completed (bool):
        True if all the files have been uploaded
    status.n_uploaded (int):
        The number of files already uploaded in this session
    status.n_total (int):
        The number of files to be uploaded.
    status.uploaded_size_mb (float):
        Size of files uploaded in Megabytes
    status.total_size_mb (float):
        Total size of files to be uploaded in Megabytes
    status.upload_id (str or None):
        The upload id used in the upload process, if any.
    """

    def __init__(
        self,
        uploaded_files: Sequence[Union[str, os.PathLike]],
        n_total: int,
        uploaded_size_mb: float,
        total_size_mb: float,
        upload_id: Optional[str] = None,
    ):
        """
        Parameters
        ---------
        uploaded_files: list of str
            The uploaded files from first to latest
        n_uploaded: int
            The number of files already uploaded in this session
        n_total (int):
            The number of files to be uploaded
        uploaded_size_mb (float):
            The size of uploaded files
        total_size_mb  (float):
            The size of all files to be uploaded
        upload_id: None or str
            The upload id used.
        """

        self.uploaded_files = [Path(x) for x in uploaded_files]
        self.latest_file = self.uploaded_files[-1]

        self.n_uploaded = len(uploaded_files)
        self.n_total = n_total
        self.upload_id = upload_id

        self.is_completed = self.n_uploaded == n_total
        if self.n_uploaded > n_total:
            warnings.warn(
                "Initializing UploadStatus with n_uploaded > n_total. This should "
                "not be happening"
            )

        self.uploaded_size_mb = uploaded_size_mb
        self.total_size_mb = total_size_mb
        self.progress = uploaded_size_mb / total_size_mb

    def to_dict(self) -> UploadStatus:
        return UploadStatus(
            uploaded_files=tuple(str(fpath) for fpath in self.uploaded_files),
            latest_file=str(self.latest_file),
            n_uploaded=self.n_uploaded,
            n_total=self.n_total,
            upload_id=self.upload_id,
            is_completed=self.is_completed,
            uploaded_size_mb=self.uploaded_size_mb,
            total_size_mb=self.total_size_mb,
            progress=self.progress,
        )

    def __str__(self):

        vals = [
            f"latest_file = {self.latest_file}",
            f"uploaded_files = [{', '.join(str(x) for x in self.uploaded_files)}]",
            f"is_completed = {self.is_completed}",
            f"n_uploaded = {self.n_uploaded}",
            f"n_total = {self.n_total}",
            f"uploaded_size_mb = {self.uploaded_size_mb}",
            f"total_size_mb = {self.total_size_mb}",
            f"progress = {self.progress}",
            f"upload_id = {self.upload_id}",
        ]
        return "<UploadStatus: " + ", ".join(vals) + ">"
