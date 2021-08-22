import typing
import string


class PluralFormatter(string.Formatter):

    def format_field(self, value: typing.Any, spec: str) -> str:
        spec_split = spec.split(",")
        if spec_split[0] == "plural":
            _, single, multiple = spec_split
            if value == 1:
                return single
            return multiple
        return super().format_field(value, spec)


class PronounFormatter(string.Formatter):

    def format_field(self, value: typing.Any, spec: str) -> str:
        spec_split = spec.split(",")
        if spec_split[0] == "pronoun":
            _, personal, other = spec_split
            if value:
                return personal
            return other
        return super().format_field(value, spec)


class Formatter(PluralFormatter, PronounFormatter):
    pass
