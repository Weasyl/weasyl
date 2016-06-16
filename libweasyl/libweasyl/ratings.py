import functools

from translationstring import TranslationString as _


@functools.total_ordering
class Rating(object):
    def __init__(self, code, character, name, nice_name, minimum_age, block_text,
                 additional_description=None):

        # public properties
        self.code = code
        self.character = character
        self.name = name
        self.minimum_age = minimum_age
        self.additional_description = additional_description

        self._nice_name = nice_name
        self._block_text = block_text

    @property
    def nice_name(self):
        """ Internationalized user facing name for this rating """
        return _(self._nice_name)

    @property
    def block_text(self):
        """ Internationalized text for blocking a rating level """
        return _(self._block_text)

    @property
    def name_with_age(self):
        """ e.g. 'Moderate (13+)': Internationalized name plus age restriction """

        info = [
            self.minimum_age and "%d+" % (self.minimum_age,),
            self.additional_description
        ]

        if any(info):
            return "%s (%s)" % (self.nice_name, " ".join(filter(bool, info)))

        return self.nice_name

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


GENERAL = Rating(10, "g", "general", "General", 0, "Block general and higher")
MODERATE = Rating(20, "m", "moderate", "Moderate", 13, "Block moderate and higher")
MATURE = Rating(30, "a", "mature", "Mature", 18, "Block mature and higher", "non-sexual")
EXPLICIT = Rating(40, "p", "explicit", "Explicit", 18, "Block explicit only", "sexual")
ALL_RATINGS = [GENERAL, MODERATE, MATURE, EXPLICIT]


CODE_MAP = {rating.code: rating for rating in ALL_RATINGS}
NAME_MAP = {rating.name: rating for rating in ALL_RATINGS}
CHARACTER_MAP = {rating.character: rating for rating in ALL_RATINGS}
CODE_TO_NAME = {rating.code: rating.name for rating in ALL_RATINGS}


def get_ratings_for_age(age):
    age = max(0, age)
    return [rating for rating in ALL_RATINGS if rating.minimum_age <= age]
