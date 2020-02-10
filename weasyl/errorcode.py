from __future__ import absolute_import

userid = "This user doesn't seem to be in our database."
submitid = "This submission doesn't seem to be in our database."
charid = "This character doesn't seem to be in our database."
journalid = "This journal doesn't seem to be in our database."

signed = "You cannot perform this operation while signed in."
unsigned = "You must be signed in to perform this operation."
permission = "You do not have permission to access this page."

token = (
    "This action appears to have been performed illegitimately; for your "
    "security, this request was not fully processed. If you believe you are "
    "receiving this message in error, return to the previous page, refresh, "
    "and try again.")
rating = (
    "This page contains content that you cannot view according to your "
    "current allowed ratings.")
friends = (
    "This page contains content that you cannot view because the page "
    "owner has allowed only friends to access it.")
no_guest_access = (
    "You cannot view this page because the owner does not allow guests to view their profile.")
unexpected = (
    "An unexpected error occurred and your request could not be "
    "fully processed.")

error_messages = {
    "addressInvalid": "Your IP address does not match the location from which this request was made.",
    "AdminLocked": "This content has been locked from any editing by an admin.",
    "ArtistTags": "You cannot remove tags that have been added by the artist.",
    "birthdayInsufficient": (
        "Your date of birth indicates that you are not allowed to set your content rating settings to the "
        "level you entered. Please choose a lower rating level."),
    "birthdayInvalid": "The date of birth you entered does not appear to be valid.",
    "CannotSelfFavorite": "You cannot favorite your own content.",
    "cannotSelfCollect": "You cannot collect a submission you have created",
    "CannotSelfReport": "You cannot report your own content.",
    "cannotIgnoreSelf": "You cannot ignore yourself.",
    "cannotIgnoreStaff": "You are not allowed to ignore this site staff member.",
    "ChangeEmailVerificationTokenIncorrect": (
        "The verification token submitted was either incorrect, or the time frame "
        "for verifying the pending email change has expired. Please attempt to change "
        "your email address once again if you still wish to change it."),
    "characterNameInvalid": "You did not enter a character name.",
    "classidInvalid": "You must select a valid commission class.",
    "collectionExists": "This submission has already been collected.",
    "collectionUnacceptable": (
        "Your collection offer could not be sent because the recipient is unable to receive it. This may "
        "be because the submission is friends-only, or the recipient's rating or filter settings prevent "
        "them from viewing it."),
    "collectionThrottle": (
        "You have too many pending collection requests for this user. "
        "Please wait for them to approve some, or ask them to offer your items to you instead."),
    "commentInvalid": "Your comment did not contain any content.",
    "commishclassExists": "This class of commissions already exists.",
    "contentInvalid": "You did not enter any content.",
    "contentOwnerIgnoredYou": "This content was posted by a user who has ignored you.",
    "coverSizeExceedsLimit": (
        "The cover art file you uploaded exceeds the allowed filesize for this submission category."),
    "coverType": (
        "The cover art file you uploaded is not a valid filetype for this submission category."),
    "duplicateSubmission": "You have already made a submission with this submission file.",
    "emailBlacklisted": (
        "The domain of the email you entered has been associated with a high volume of spam. "
        "Consequently, registrations from this domain have been blacklisted."),
    "emailExists": "The email you entered is already taken by another user.",
    "emailIncorrect": "The email you entered is not associated with the account you specified.",
    "emailInvalid": "The email you entered does not appear to be valid.",
    "emailMismatch": "The email you entered did not match the email confirmation.",
    "embedlinkInvalid": "The embed link you entered does not point to a valid resource or supported service.",
    "FeatureDisabled": "This feature has been temporarily disabled.",
    "FileType": "The file you uploaded is not of a valid type.",
    "folderRecordExists": "A folder by this name already exists.",
    "folderRecordMissing": "The specified folder does not exist.",
    "forgotpasswordRecordMissing": (
        "This link does not appear to be valid. It may have expired, meaning that you should return to the "
        "forgot password page and resubmit the form, or you may have copied the link incorrectly."),
    "FriendsOnly": friends,
    "characterRecordMissing": charid,
    "googleDocsEmbedLinkInvalid": "The Google Drive link you provided is invalid.",
    "httpError": "An error occurred while making an HTTP request on your behalf.",
    "IgnoredYou": "This user has ignored you.",
    "imageDecodeError": "The image you uploaded was unable to be decoded.",
    "InsufficientPermissions": permission,
    "insufficientActionPermissions": "You do not have permission to perform this action.",
    "journalRecordMissing": journalid,
    "logincreateRecordMissing": "That's not a valid token!",
    "loginInvalid": "The login credentials you entered were not correct.",
    "loginRecordMissing": (
        "The username you entered does not appear to be correct. Check to make sure that you entered the "
        "name correctly and that the account you are trying to recover the password for actually exists."),
    "maxamountInvalid": "The maximum amount you entered is not valid.",
    "minamountInvalid": "The minimum amount you entered is not valid.",
    "noCover": "No cover exists for that submission.",
    "noImageSource": "No image exists from which to create a thumbnail.",
    "not-utf8": "Text submissions must be encoded in UTF-8.",
    "notEnoughTags": (
        "You must maintain at least two tags on this content in order to sufficiently describe it "
        "for our search system."),
    "noteRecordMissing": "That note doesn't seem to be in our database.",
    "noThumbnail": "No thumbnail exists for that submission.",
    "noUser": "There is no such user with that name.",
    "pageOwnerIgnoredYou": "The owner of this page has ignored you.",
    "parentidInvalid": "The specified parent folder does not exist.",
    "passwordIncorrect": "The password you entered was incorrect.",
    "passwordInsecure": "Passwords must be at least 10 characters in length.",
    "passwordMismatch": "The password you entered did not match the password confirmation.",
    "priceidInvalid": "You did not specify a price to edit.",
    "RatingExceeded": rating,
    "ratingInvalid": "The specified rating is invalid.",
    "recipientExcessive": "You specified too many recipients for this message.",
    "recipientInvalid": (
        "Your message could not be delivered because you did not specify any valid recipients. The users "
        "you specified may restrict who can send them private messages, or you might be on their ignore list."),
    "RecordMissing": "That doesn't appear to exist in our database.",
    "releaseInvalid": "The release date specified is invalid.",
    "replyRecipientIgnoredYou": "The user you're replying to has ignored you.",
    "ReportCommentRequired": "This report type requires a comment",
    "shoutRecordMissing": "This shout doesn't seem to exist in our database.",
    "SpamFilteringDisabled": "Spam filtering is disabled (is the site configuration file configured correctly?).",
    "SpamFilteringDelayed": "Your post has been successfully received, and is pending moderator approval.",
    "SpamFilteringDropped": "Your post has been rejected due to similarity to spam. If you feel this rejection is "
                            "in error, please contact support, and include the exact content you attempted to post.",
    "streamDurationNotSet": "Please set a stream length.",
    "streamDurationOutOfRange": "Please enter a number up to 360 minutes for stream length.",
    "streamLocationNotSet": "Please set a stream location.",
    "submissionRecordMissing": submitid,
    "submitSizeExceedsLimit": (
        "The submission file you uploaded exceeds the allowed filesize for this submission category."),
    "submitSizeZero": "You must provide a submission file.",
    "submitType": "The submission file you uploaded is not a valid filetype for this submission category.",
    "TagBlocked": "This submission's assigned tags suggest that it may contain content you do not wish to view.",
    "TargetRecordMissing": "This content doesn't seem to exist in our database.",
    "thumbSizeExceedsLimit": (
        "The thumbnail file you uploaded exceeds the allowed filesize for this submission category."),
    "thumbType": "The thumbnail file you uploaded is not a valid image filetype.",
    "TimeLimitExceeded": "You can't edit that any longer.",
    "titleExists": "That title is already being used.",
    "titleInvalid": "You did not enter a title.",
    "titleTooLong": "That title is too long.",
    "tooManyPreferenceTags": "You cannot have more than 50 preference tags.",
    "TwoFactorAuthenticationAuthenticationAttemptsExceeded": (
        "You have incorrectly entered your 2FA token or recovery code too many times. Please try logging in again."),
    "TwoFactorAuthenticationAuthenticationTimeout": "Your authentication session has timed out. Please try logging in again.",
    "TwoFactorAuthenticationRequireEnabled": "Two-Factor Authentication must be enabled to access this page.",
    "TwoFactorAuthenticationRequireDisbled": "Two-Factor Authentication must not be enabled to access this page.",
    "TwoFactorAuthenticationZeroRecoveryCodesRemaining": (
        "Your account had zero recovery codes remaining, and as such 2FA was disabled to prevent "
        "you from being permanently unable to log into your account. You may re-enable 2FA if you desire to do so."),
    "unknownMessageFolder": "The specified message folder does not exist.",
    "UserIgnored": "This content was posted by a user you have chosen to ignore.",
    "userRecordMissing": userid,
    "usernameExists": "The username you entered is already registered by another user.",
    "usernameIncorrect": "The username you entered does not match the account for which this request was made.",
    "usernameInvalid": (
        "The username you entered is not valid. Usernames must contain one or more alphanumeric characters."),
    "vouchRequired": (
        "Your account has to be verified to do that."
        " [How do I verify my account?](/help/verification)"),
    "watchuserRecordMissing": "You are not following the specified user.",
    "YouIgnored": "You have this user ignored.",
    "youIgnoredPageOwner": "You have the owner of this page ignored.",
    "youIgnoredReplyRecipient": "You are ignoring the user you're replying to.",
}

# If an error code defined in error_messages should return a special HTTP status code,
# put it here. Errors without a corresponding entry in this list will use
# the default status code.
error_status_code = {
    "userRecordMissing": 404,
    "submissionRecordMissing": 404,
    "journalRecordMissing": 404,
    "characterRecordMissing": 404,
    "vouchRequired": 403,
}


login_errors = {
    "invalid": "The username or password provided was incorrect.",
    "banned": "Your account has been permanently banned.",
    "suspended": "Your account has been temporarily suspended.",
    "unicode-failure": "Your password was stored poorly. You must reset it using the forgotten password page.",
}
