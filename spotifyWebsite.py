from flask import Flask, request, render_template, redirect
from flask.helpers import url_for
import requests
import base64
 
s = requests.session()
clientID="743e391dfa9a4581beb6266c2fbe408a"  # Client ID and Secret for Spotify API use
clientSecret=""  # Code will not work without secret - use link in README to see/use the website in action

app = Flask(__name__)  # Setup for Flask app

@app.route("/")  # Home page and button for logging into Spotify
def login():
    parameters={'client_id':clientID,'response_type':'code','redirect_uri':'http://127.0.0.1:5000/access','scope':'user-top-read','show_dialog':'true'}  # Parameters to get authorization code
    BaseURL='https://accounts.spotify.com/authorize'
    r=s.get(BaseURL, params=parameters)
    return render_template("login.html",url=r.url)

@app.route("/home/<token>")  # The main returning point to choose different features after being logged in.
def home(token):
    return render_template("home.html",token=token)

@app.route("/access")  # Endpoint for user login and going to home page
def access():
    code=request.args.get('code')  # Setup for retrieving authorization code/access token
    parameters={"grant_type":"authorization_code","code":code,"redirect_uri":'http://127.0.0.1:5000/access'}
    authHeader=base64.urlsafe_b64encode((clientID+":"+clientSecret).encode('ascii'))
    headers={"Authorization":"Basic %s" %authHeader.decode('ascii'), "Content-Type":"application/x-www-form-urlencoded"}
    r=s.post('https://accounts.spotify.com/api/token',headers=headers,data=parameters)
    if 'error' in r.json():  # If user does not agree to terms
        return render_template("errorLogin.html")  # Show error with login page, with button to return back to welcome/home page
    access=r.json()['access_token']  # Access token to be used to get info on Spotify user
    return redirect(url_for('home',token=access))

def checkTest(token):  # Function to check if the current account is the test account
    header={'Authorization':'Bearer '+token, "Content-Type":"application/json"}
    r=s.get("https://api.spotify.com/v1/me",headers=header)
    if r.json()["display_name"]=="TestAccount":
        return True
    else:
        return False    

def getReco(token,amount,trackID,artistID):
    header={'Authorization':'Bearer '+token}
    r=s.get("https://api.spotify.com/v1/artists/"+artistID,headers=header)  # Get request for top artist information
    artistInfo=r.json()  # Info on artist from get request
    genre=artistInfo['genres']  # Genre(s) of top track's artist to be used for recommendation
    r=s.get("https://api.spotify.com/v1/recommendations",headers=header,params={"limit":int(amount),'seed_artists':artistID,'seed_tracks':trackID,'seed_genre':genre})  # Get request for recommendation songs using seeds from top tracks 
    RecommendedSongs={}  # Dictionary to hold each recommened songs and their respective artists
    for i in range(int(amount)):  # Loop for adding in recommended songs and artists into dictionary
        artists=""  # Empty string to fill in artists for sibg
        for a in range(len(r.json()['tracks'][i]['artists'])):
            artists+=r.json()['tracks'][i]['artists'][a]['name']+", "
        artists=artists[:len(artists)-2]  # Take out last comma and space for the last song
        RecommendedSongs[r.json()['tracks'][i]['name']]=" --- By: "+artists  # Assign string of artists to the key of the recommended song
    return RecommendedSongs

def getKey(keyNum):  # Function for determining key of song
    if keyNum==0:
        key="C"
    elif keyNum==1:
        key="C#/D♭"
    elif keyNum==2:
        key="D"
    elif keyNum==3:
        key="D#/E♭"
    elif keyNum==4:
        key="E"
    elif keyNum==5:
        key="F"
    elif keyNum==6:
        key="F#/G♭"
    elif keyNum==7:
        key="G"
    elif keyNum==8:
        key="G#/A♭"
    elif keyNum==9:
        key="A"
    elif keyNum==10:
        key="A#/B♭"
    elif keyNum==11:
        key="B"
    elif keyNum==-1:  # No key determined
        key="N/A"     
    return key                     

def getMode(modeNum):  # Function to get modality of track
    if modeNum==1:
        return "Major"
    elif modeNum==0:
        return "Minor"    

@app.route("/songs/<token>/<top>/<recom>")  # Feature for webpage: Top songs + recommendations for each
def songs(token, top, recom):
    topWithReco={}  # Dictionary to hold top songs with dictionary holding 5 recommended songs each
    header={'Authorization':'Bearer '+token}
    if checkTest(token):  # If test account
        r=s.get("https://api.spotify.com/v1/me/top/tracks",headers=header,params={"limit":int(top),"time_range":"long_term"})  # Get request for top songs of test account
    else:  # Not test account uses short term
        r=s.get("https://api.spotify.com/v1/me/top/tracks",headers=header,params={"limit":int(top),"time_range":"short_term"})  # Get request for top songs of user
    topTracks=r.json()  # Top songs info from get request
    if "error" in topTracks:  # Error handing with account
        return render_template("error.html",token=token)
    for x in range(int(top)):  # Going through each top song
        trackID=topTracks['items'][x]['id']
        artistID=topTracks['items'][x]['artists'][0]['id']
        artists=""  # Empty string to hold artist(s) names
        for a in range(len(topTracks['items'][x]['artists'])):  # Going through each artist
            artists+=topTracks['items'][x]['artists'][a]['name']+", "  # Adding commas to spearate names
        artists=artists[:len(artists)-2]  # Taking out last comma as it's the last artist in the string
        topWithReco[topTracks['items'][x]['name']+" --- By: "+artists]=getReco(token,recom,trackID,artistID)  # Assign recommened songs+artists dictionary to main dictionary
    return render_template("songs.html",songs=topWithReco,token=token) 

@app.route("/analytics/<token>/<top>")  # Endpoint for accessing feature/analytic values for top songs
def anayltics(token,top):
    topWithAnalytics={}  # Dictionary to hold each top song with their respective feature/analytical values
    header={'Authorization':'Bearer '+token}
    if checkTest(token):  # If test account
        r=s.get("https://api.spotify.com/v1/me/top/tracks",headers=header,params={"limit":int(top),"time_range":"long_term"})  # Get request for top songs of test account
    else:  # Not test account uses short term
        r=s.get("https://api.spotify.com/v1/me/top/tracks",headers=header,params={"limit":int(top),"time_range":"short_term"})  # Get request for top songs of user
    topTracks=r.json()  # Top songs info from get request
    if "error" in topTracks:  # Error handling with account
        return render_template("error.html",token=token)
    for x in range(int(top)):
        trackID=topTracks['items'][x]['id']  # Top Song ID
        header={'Authorization':'Bearer '+token,'Content-Type':'application/json'} # Header for GET request
        r=s.get("https://api.spotify.com/v1/audio-features/"+trackID,headers=header)  # GET request for track details
        features=r.json()
        artists=""  # Empty string to hold artist(s) names
        for a in range(len(topTracks['items'][x]['artists'])):  # Going through each artist
            artists+=topTracks['items'][x]['artists'][a]['name']+", "  # Adding commas to spearate names
        artists=artists[:len(artists)-2]  # Taking out last comma as it's the last artist in the string
        if 'error' in features:  # No features for this specific song
            topWithAnalytics[topTracks['items'][x]['name']+" --- By: "+artists]=["N/A","N/A","N/A","N/A","N/A","N/A","N/A"] # No values for this song. 
        else:
            dancePercent=features['danceability']  # Danceability decimal from json response
            dancePercent*=100  # Turn decimal into percentage
            positivePercent=features['valence']  # Positivity decimal from json response
            positivePercent*=100  # Turn decimal into percentage
            energyPercent=features['energy']  # Energy decimal from json response
            energyPercent*=100  # Turn decimal into percentage
            tempo=features['tempo']  # Tempo of song
            signature=features['time_signature']  # Time Signature of song
            keyNum=features['key']  # Number of key song is in
            key=getKey(keyNum)  # Calling function to return key using number of key
            modeNum=features['mode']  # Modality (Major or minor)
            modality=getMode(modeNum)  # Calling function to get modality of track         
            topWithAnalytics[topTracks['items'][x]['name']+" --- By: "+artists]=[str(round(dancePercent))+"%",str(round(energyPercent))+"%",str(round(positivePercent))+"%",str(tempo)+" BPM",str(signature)+"/4",key,modality]  # Assign all percents to key of track name + artist
    return render_template("analytics.html",songs=topWithAnalytics,token=token)          

@app.route("/search/<token>/<query>")  # Search endpoint for searching songs
def search(token,query):
    query=query.replace("-------","?")  # Replacements for characters that mess up URL loading
    query=query.replace("------","#")
    query=query.replace("-----","/")
    results={}  # Dictionary to hold search results (song names and artists)
    header={'Authorization':'Bearer '+token}
    r=s.get("https://api.spotify.com/v1/search",headers=header,params={"q":query,"type":"track,artist","limit":15})
    searchResp=r.json()  # Response from GET request for search
    for i in range(len(searchResp['tracks']['items'])):  # Loop for adding in search query songs and artists into dictionary
        songInfo={}  # Dictionary to hold all song info for respective search query song
        trackID=searchResp['tracks']['items'][i]['id']  # Track's ID
        artistID=searchResp['tracks']['items'][i]['artists'][0]['id']  # Artist ID for this track
        songInfo["trackID"]=trackID  # Adding track ID to songInfo dictionary
        songInfo["artistID"]=artistID  # Adding artist ID to songInfo dictionary
        analytics={}  # Dictionary that holds all analytic values for each searched song
        header={'Authorization':'Bearer '+token,'Content-Type':'application/json'} # Header for GET request
        r=s.get("https://api.spotify.com/v1/audio-features/"+trackID,headers=header)  # GET request for track details
        features=r.json()
        if 'error' in features:  # No features for this specific song
            analytics["positive"]="N/A"
            analytics["dance"]="N/A"
            analytics["energy"]="N/A"
            analytics["tempo"]="N/A"
            analytics["time"]="N/A"
            analytics["key"]="N/A"
            analytics["mode"]="N/A"
        else:   
            positivePercent=features['valence']  # Positivity decimal from json response
            positivePercent*=100  # Turn decimal into percentage
            analytics["positive"]=str(round(positivePercent))+"%"  # Add positivity to analytics dictionary
            dancePercent=features['danceability']  # Danceability decimal from json response
            dancePercent*=100  # Turn decimal into percentage
            analytics["dance"]=str(round(dancePercent))+"%"  # Add danceability to analytics dictionary
            energyPercent=features['energy']  # Energy decimal from json response
            energyPercent*=100  # Turn decimal into percentage
            analytics["energy"]=str(round(energyPercent))+"%"  # Add energy to analytics dictionary
            tempo=features['tempo']  # Tempo of song
            analytics["tempo"]=str(tempo)+" BPM"
            signature=features['time_signature']  # Time Signature of song
            analytics["time"]=str(signature)+"/4"
            keyNum=features['key']  # Number of key song is in
            analytics["key"]=getKey(keyNum)  # Calling function to get string of key of track
            modeNum=features['mode']  # Modality value of song
            analytics["mode"]=getMode(modeNum)  # Calling function to get string of modality of track
        songInfo["analytics"]=analytics
        artists=""  # Empty string to hold artist(s) names
        for a in range(len(searchResp['tracks']['items'][i]['artists'])):  # Going through each artist
            artists+=searchResp['tracks']['items'][i]['artists'][a]['name']+", "  # Adding commas to spearate names
        artists=artists[:len(artists)-2]  # Taking out last comma as it's the last artist in the string
        songInfo["artists"]=" --- By: "+artists  # Adding in artist's string to songInfo dictionary
        results[searchResp['tracks']['items'][i]['name']]=songInfo # Assign string of artists to the key of the search query song    
    return render_template("search.html",songs=results,token=token,query=query)

@app.route("/searchRecom/<token>/<recom>/<name>/<artists>/<trackID>/<artistID>")  # Endpoint for searched-song recommendations
def searchRecom(token,recom,name,artists,trackID,artistID):
    name=name.replace("-------","?")  # Replacements for characters in track that mess up URL loading
    name=name.replace("------","#")
    name=name.replace("-----","/")
    artists=artists.replace("-------","?")  # Replacements for characters in artist that mess up URL loading
    artists=artists.replace("------","#")
    artists=artists.replace("-----","/")
    searchWithReco={}  # Total dictionary to hold searched song name, artist, and recommendation dictionary
    RecommendedSongs={}  # Initializaing recommendation dictionary
    RecommendedSongs=getReco(token,recom,trackID,artistID)  # Calling recommendations function
    searchWithReco[name+artists]=RecommendedSongs  # Assigning searched song+artist key to recommendation dictionary value
    return render_template("searchRecom.html",token=token,songs=searchWithReco)

if __name__ == '__main__':
  app.run(debug = True)
