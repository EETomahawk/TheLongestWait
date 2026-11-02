#Python 3.10

from urllib.request import Request, urlopen
import re
from datetime import datetime, timedelta

url = "https://forums.everybodyedits.com/viewtopic.php?id=47849"
selector = "/viewtopic.php?id=47849"
html = ""
r = Request(url=url, headers={'User-Agent': 'Mozilla/5.0'})

#Regex to find next page button in thread.
nextPageRegex = r'<a rel="next"'

#Regex to match username within "<span class...>USERNAME</span>".
regexUsername = r"<span class[^>]*>([^<]+)</span>"

#Regex to find all post timestamps.
regexPostTimestamp = (r'<a href="viewtopic\.php\?id=47849&p=\d+#p\d{6}">' #First part of URL containing post timestamp.
                      r'(Today |Yesterday )?' #Optional capture group for posts from "Today" or "Yesterday".
                      r'([^<]+)' #Capture group for timestamp: either YYYY-MM-DD HH:MM:SS or just HH:MM:SS.
                      r'</a>') #End of hyperlink.

dates = { "Today ": datetime.today().date(),
          "Yesterday ": datetime.today().date() - timedelta(days=1)}

posts = [] #List of tuples containing (timestamp, author).
currentPageNumber = 1
reachedLastPage = False

while not reachedLastPage:

    r.selector = f"{selector}&p={currentPageNumber}" #Select which forum page to browse.
    html = urlopen(r).read().decode("utf8")  #Scrape raw HTML of forum page.

    for match in re.finditer(regexPostTimestamp, html): #Iterate over each post on page.

        day = match.group(1) #Post is from Yesterday or Today or neither(=None).
        timeOrTimestamp = match.group(2) #Either YYYY-MM-DD HH:MM:SS or just HH:MM:SS.

        if day is not None: #Timestamp is "Today" or "Yesterday" followed by time of day.
            time = datetime.strptime(timeOrTimestamp, "%H:%M:%S").time() #Parse time of day.
            timestamp = datetime.combine(dates[day], time).timestamp() #Build unix timestamp.
        else: #Post is older than Yesterday.
            timestamp = datetime.strptime(timeOrTimestamp, "%Y-%m-%d %H:%M:%S").timestamp() #Unix timestamp.

        #Extract username from HTML slightly after the timestamp.
        author = re.search(regexUsername, html[match.end(2):]).group(1)

        posts.append((timestamp, author)) #Record post's unix timestamp and its author's username.

    #Check if Next page button exists on current page.
    if re.search(nextPageRegex, html): currentPageNumber += 1
    else: reachedLastPage = True

longestDeltas = {} # { "username" = unixDelta, ... }
shortestDeltas = {}

for i in range(1, len(posts)): #For each post.
    
    name = posts[i][1] #Author username.
    delta = posts[i][0] - posts[i-1][0] #Time elapsed since previous post.

    #Save longest delta for each poster.
    if name not in longestDeltas or delta > longestDeltas[name]:
        longestDeltas[name] = delta
    
    #Save shortest delta. Ignore doubleposts.
    if (name not in shortestDeltas or delta < shortestDeltas[name]) and name != posts[i-1][1]:
        shortestDeltas[name] = delta
       
print("[b]The Longest Wait[/b]:\n[code]") #Build BBcode-formatted scoreboard post.

#Rank and iterate top ten Longest Waiters.
for i, (name, delta) in enumerate(sorted(longestDeltas.items(), key=lambda x: -x[1])[:10], start=1):
    #Print rank, time duration and username.
    s = f"{i:>2}. {str(timedelta(seconds=delta))} - {name}"
    if s[14] == ":": s = f"{s[:13]}0{s[13:]}" #Pad number of hours to 2 digits.
    print(s)

print("[/code]\n[b]The Shortest Wait[/b] (Minutes:Seconds):\n[code]")

for i, (name, delta) in enumerate(sorted(shortestDeltas.items(), key=lambda x: x[1])[:10], start=1):
    print(f"{i:>2}. {str(timedelta(seconds=delta))[2:]} - {name}") #Print rank, time duration and username.

print("[/code]")