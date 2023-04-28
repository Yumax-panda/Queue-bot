from typing import TYPE_CHECKING, Optional

class MyError(Exception):
    """An error that can be localized."""

    __slots__ = ("localizations", )

    if TYPE_CHECKING:
        localizations: dict[str, str]

    def __init__(self, localizations: dict[str, str]) -> None:
        self.localizations = localizations

    def localize(self, locale: Optional[str]) -> str:
        default = "\n".join(self.localizations.values())
        return self.localizations.get(locale, default)


class InvalidPlayerNum(MyError):

    def __init__(self, allowed_num: int = 12):
        super().__init__(
            {"ja": f"プレイヤー数は{allowed_num}人のみです。", "en-US": f"Player number must be {allowed_num}."}
        )