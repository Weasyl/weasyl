import functools
from collections.abc import Collection


@functools.total_ordering
class Rating:
    def __init__(self, code, character, name, nice_name, minimum_age, block_text,
                 additional_description=None):

        self.code = code
        self.character = character
        self.name = name
        self.minimum_age = minimum_age
        self.additional_description = additional_description
        self.nice_name = nice_name
        self.block_text = block_text

        info = [
            self.minimum_age and "%d+" % (self.minimum_age,),
            self.additional_description
        ]

        if any(info):
            self.name_with_age = "%s (%s)" % (self.nice_name, " ".join(filter(bool, info)))
        else:
            self.name_with_age = self.nice_name

    def __repr__(self):
        return "Rating:" + self.name

    def __eq__(self, other):
        if not isinstance(other, Rating):
            return NotImplemented
        return self.code == other.code

    def __lt__(self, other):
        if not isinstance(other, Rating):
            return NotImplemented
        return self.code < other.code

    def __hash__(self):
        return self.code

    @property
    def is_adult(self) -> bool:
        """
        Whether this rating is restricted to adults.
        """
        return self > GENERAL


GENERAL = Rating(10, "g", "general", "General", 0, "Block all ratings")
MATURE = Rating(30, "a", "mature", "Mature", 18, "Block Mature and higher", "non-sexual")
EXPLICIT = Rating(40, "p", "explicit", "Explicit", 18, "Block Explicit only", "sexual or harder fetishes")
ALL_RATINGS = [GENERAL, MATURE, EXPLICIT]


CODE_MAP = {rating.code: rating for rating in ALL_RATINGS}
CHARACTER_MAP = {rating.character: rating for rating in ALL_RATINGS}
CODE_TO_NAME = {rating.code: rating.name for rating in ALL_RATINGS}


def get_ratings_for_age(age: int | None) -> Collection[Rating]:
    if age is None:
        return ALL_RATINGS

    age = max(0, age)
    return [rating for rating in ALL_RATINGS if rating.minimum_age <= age]
