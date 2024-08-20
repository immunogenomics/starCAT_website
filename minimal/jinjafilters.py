from inflection import parameterize
from flask import g,Markup

def slugify(myvar):
    return parameterize(myvar)[:80].rstrip('-')

#This data would better go in a database...
errorDict = { 
    "Err1": "ERROR 1: watch out for error n.1!",
    "Err2": "ERROR 2: watch out for error n.2!",
    "Err9": "ERROR 9: watch out for error n.9!"
}

def displayError(errNum):
    key = "Err"+str(errNum)
    result = errorDict[key]
    return result


msgDict = { 
    "Msg1": "<p>This is a <b>nice</b> message, the first of the list</p>",
    "Msg2": "<p>This is an even <b>nicer</b> message.</p>",
    'select_ref_message' : '<p>Please first submit a reference catalog selection and upload again.</p>',
    'Login Unsuccessful. Please check email and password and make sure you have already registered.' : '<p>Login Unsuccessful. Please check email and password and make sure you have already registered.</p>',
    'Your account has been created! You can now log in.' : '<p>Your account has been created! You can now log in.</p>'

    # 'processing_message' : '<p>Your data is processing.</p>',
    
}

def displayMessage(msgKey):
    #THE DECORATOR IS NEEDED TO DISABLE CACHING OF JINJA CALLS!!!
    result = Markup(msgDict[msgKey])
    return result
