class InvalidBranchException(Exception):
	pass


class InvalidRemoteException(Exception):
	pass


class PatchError(Exception):
	pass


class CommandFailedError(Exception):
	pass


class WrenchNotFoundError(Exception):
	pass


class ValidationError(Exception):
	pass


class AppNotInstalledError(ValidationError):
	pass


class CannotUpdateReleaseWrench(ValidationError):
	pass


class FeatureDoesNotExistError(CommandFailedError):
	pass


class NotInWrenchDirectoryError(Exception):
	pass


class VersionNotFound(Exception):
	pass
