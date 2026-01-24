from weasyl import macro as m


userid = "This user doesn't seem to be in our database."
submitid = "This submission doesn't seem to be in our database."
charid = "This character doesn't seem to be in our database."
journalid = "This journal doesn't seem to be in our database."

signed = "You cannot perform this operation while signed in."
unsigned = "You must be signed in to perform this operation."
permission = "You do not have permission to access this page."

token = (
    "We weren’t able to process your request for security reasons. If you’re seeing this error after trying to perform an action on Weasyl, your web browser may not be compatible with this website. We recommend [Firefox](https://www.mozilla.org/firefox/) or [Chrome](https://www.google.com/chrome/).")
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
    "birthdayInconsistentWithRating": (
        "You’ve already confirmed that you were 18 or older when setting rating preferences or a post’s rating; Weasyl won’t show an age inconsistent with that on your profile."),
    "birthdayInconsistentWithTerms": (
        "You’ve already confirmed that you were 13 or older when signing up; Weasyl won’t show an age inconsistent with that on your profile."),
    "birthdayInsufficient": (
        "Your date of birth indicates that you are not allowed to set your content rating settings to the "
        "level you entered. Please choose a lower rating level."),
    "birthdayInvalid": "The date of birth you entered does not appear to be valid.",
    "CannotSelfFavorite": "You cannot favorite your own content.",
    "cannotSelfFollow": "You cannot follow yourself.",
    'cannotSelfFriend': "You cannot friend yourself.",
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
    "crosspostInvalid": (
        "The image you crossposted was from an unsupported source. "
        "Please report this bug to the creator of the crossposting tool."),
    "duplicateSubmission": "You have already made a submission with this submission file.",
    "emailBlacklisted": (
        "The domain of the email you entered has been associated with a high volume of spam. "
        "Consequently, registrations from this domain have been blacklisted."),
    "emailIncorrect": "The email you entered is not associated with the account you specified.",
    "emailInvalid": "The email you entered does not appear to be valid.",
    "embedlinkFailed": "Weasyl failed to load the embed link you entered. It might be a broken or unsupported link, or this might be a temporary communication failure between Weasyl and the other service. Please check your link and try again later.",
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
    "globalLimit": f"Weasyl hit an internal limit unexpectedly and can’t process your request right now. Please report this bug to [{m.MACRO_SUPPORT_ADDRESS}](mailto:{m.MACRO_SUPPORT_ADDRESS}), and try again later.",
    "googleDocsEmbedLinkInvalid": (
        "The link you provided isn’t a valid Google Docs embed link."
        " If you’re not sure which link to use, we have [a guide on publishing documents from Google Docs](/help/google-drive-embed) that might help."
    ),
    "hiddenFavorites": "You cannot view this page because the owner does not allow anyone to see their favorites.",
    "httpError": "An error occurred while making an HTTP request on your behalf.",
    "IgnoredYou": "This user has ignored you.",
    "imageDecodeError": "The image you uploaded was unable to be decoded.",
    "InsufficientPermissions": permission,
    "insufficientActionPermissions": "You do not have permission to perform this action.",
    "journalRecordMissing": journalid,
    "logincreateRecordMissing": "That's not a valid token!",
    "maxamountInvalid": "The maximum amount you entered is not valid.",
    "minamountInvalid": "The minimum amount you entered is not valid.",
    'noGuests': no_guest_access,
    "noCover": "No cover exists for that submission.",
    "noImageSource": "No image exists from which to create a thumbnail.",
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
    "priceidInvalid": "You did not specify a price to edit.",
    "RatingExceeded": rating,
    "ratingInvalid": "The specified rating is invalid.",
    "recipientExcessive": "Private messages can only be sent to one recipient at a time.",
    "recipientInvalid": (
        "Your message could not be delivered because you did not specify any valid recipients. The users "
        "you specified may restrict who can send them private messages, or you might be on their ignore list."),
    "RecordMissing": "That doesn't appear to exist in our database.",
    "releaseInvalid": "The release date specified is invalid.",
    "replyRecipientIgnoredYou": "The user you're replying to has ignored you.",
    "ReportCommentRequired": "This report type requires a comment",
    "shoutRecordMissing": "This shout doesn't seem to exist in our database.",
    "signed": signed,
    "streamDurationNotSet": "Please set a stream length.",
    "streamDurationOutOfRange": "Please enter a number up to 360 minutes for stream length.",
    "streamLocationNotSet": "Please set a stream location.",
    "streamLocationInvalid": "The stream location you entered is not a valid link.",
    "submissionRecordMissing": submitid,
    "submitSizeExceedsLimit": (
        "The submission file you uploaded exceeds the allowed filesize for this submission category."),
    "submitSizeZero": "You must provide a submission file.",
    "submitType": "The submission file you uploaded is not a valid filetype for this submission category.",
    "TagBlocked": "This submission's assigned tags suggest that it may contain content you do not wish to view.",
    "tagTooLong": "A tag you entered was too long (>100 characters). Please check that your tags are formatted correctly (separated with commas or spaces).",
    "TargetRecordMissing": "This content doesn't seem to exist in our database.",
    "thumbSizeExceedsLimit": (
        "The thumbnail file you uploaded exceeds the allowed filesize for this submission category."),
    "thumbType": "The thumbnail file you uploaded is not a valid image filetype.",
    "titleExists": "That title is already being used.",
    "titleInvalid": "You did not enter a title.",
    "titleTooLong": "That title is too long.",
    "token": token,
    "tooManyPreferenceTags": "You cannot have more than 50 preference tags.",
    "turnstileMissing": (
        "A required bot check failed. Please go back, refresh the page, and try again.\n\n"
        f"If issues persist, contact support at [{m.MACRO_SUPPORT_ADDRESS}](mailto:{m.MACRO_SUPPORT_ADDRESS})."),
    "TwoFactorAuthenticationAuthenticationAttemptsExceeded": (
        "You have incorrectly entered your 2FA token or recovery code too many times. Please try logging in again."),
    "TwoFactorAuthenticationAuthenticationTimeout": "Your authentication session has timed out. Please try logging in again.",
    "TwoFactorAuthenticationRequireEnabled": "Two-Factor Authentication must be enabled to access this page.",
    "TwoFactorAuthenticationRequireDisbled": "Two-Factor Authentication must not be enabled to access this page.",
    "TwoFactorAuthenticationZeroRecoveryCodesRemaining": (
        "Your account had zero recovery codes remaining, and as such 2FA was disabled to prevent "
        "you from being permanently unable to log into your account. You may re-enable 2FA if you desire to do so."),
    "unsigned": unsigned,
    "unknownMessageFolder": "The specified message folder does not exist.",
    "UserIgnored": "This content was posted by a user you have chosen to ignore.",
    "userRecordMissing": userid,
    "usernameChangedTooRecently": "You can't change your username within 30 days of a previous change.",
    "usernameBanned": (
        "The username you entered is reserved. Please choose a different username."),
    "usernameExists": "The username you entered is already registered by another user.",
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
    "globalLimit": 503,
    'InsufficientPermissions': 403,
    "userRecordMissing": 404,
    "submissionRecordMissing": 404,
    "journalRecordMissing": 404,
    "characterRecordMissing": 404,
    "vouchRequired": 403,
    "signed": 403,
    "unsigned": 403,
    "token": 403
}
