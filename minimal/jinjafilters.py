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

def displayMessage(msgKey):
    #THE DECORATOR IS NEEDED TO DISABLE CACHING OF JINJA CALLS!!!
    result = Markup(msgKey)
    return result
