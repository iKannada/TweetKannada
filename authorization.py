import tweepy


def authorize_user(app_key, app_secret):
    auth = tweepy.OAuthHandler(app_key, app_secret)
    try:
        redirect_url = auth.get_authorization_url()
        print redirect_url
    except tweepy.TweepError:
        print 'Error! Failed to get request token.'
    verifier = raw_input("Input verifier code:")
    try:
        auth.get_access_token(verifier)
    except tweepy.TweepError:
        print 'Error! Failed to get access token.'
    return auth
