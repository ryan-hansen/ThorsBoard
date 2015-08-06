# ThorsBoard
Team and score update system for thorsboard.com

ThorsBoard.com is, in simplest terms, a super-fan's "guess the score" game centered around NCAA football.  
Players show allegiance to their favorite college football team by creating a group for that and inviting their 
friends to join the group.  Each week that their team has a game, members of the group are given the chance to
try to predict the final score.  Once the final whistle blows, the system determines the week's winner using 
a super-secret proprietary algorithm that identifies the prediction nearest the actual outcome. 

Prizes are awarded to each weekly winner, as well as to the season's best overall performer.

The challenge that thorsboard.com faces is to keep up with division and conference changes for each team (which are more
frequent than you might think), and more importantly, to keep up with game outcomes each week for each team.  This
represents a formidable amount of data management each week, and as there are no free sports scores API's available at
present--thorsboard.com being a free game with no revenue or capital to fund its ongoing development and maintenance--
the only options are to handle all of the changes manually or to create some form of automated update system as a
"best effort" option that can be monitored and corrected by humans as necessary.

This project represents an attempt at that "best effort" option.  Using various Python libraries and publicly accessible
web resources, it "scrapes" the required information and updates the teams and scores accordingly.  It is an admittedly
fragile system, as it relies heavily on specific layout and style designations (CSS classes, HTML tags, etc) to identify
the data it seeks; but as those style elements do not tend to change regularly--at least not while the season is
underway--it is actually reasonably successful at keeping thorsboard.com running smoothly as an automated game system,
not requiring much manual intervention at all throughout a given season.
c