# Introduction
With the spread of communication technology there arised a multitude of new ways to spread and consume information online.
One such form are online news websites, promising to share just the real, objective facts on matters of interest for the 
average web surfer.

But our world is definitely not perfect. There also appeared something of interest especially for the monetization-oriented:
 virtually (pun intended) unlimited advertising space. And what does the capitalist do when he has something of value? He sells.
And sell did they, with the online advertising industry being worth USD 236.90 billion as of 2022 ([source](https://www.grandviewresearch.com/industry-analysis/online-advertising-market-report#:~:text=The%20global%20online%20advertising%20market,and%20transformation%20in%20recent%20years)).

And so, blinded by the possibility of raking up profit from selling on-site space for ads by pay-per-click and other means, 
news outlets had to somehow gain more, well, clicks. They started using people's emotions, stirring up disbelief, hate and other
nasty sentiments just to get them to click the article. They were so good at it in fact that the emotion-bending didn't stop
at just click-baity titles, but quickly spread to the whole article, leading us to having to deal with "UNBELIEVEABLE! THE MILLIONAIRE
CRASHED THE BOLIDE IN A STREET RACE" instead of seeing "Local man bends lightpost while backing up his 2002 Honda Accord".

# Motivation
As mentioned above, the spread of news that play with people's emotion and tendency to seek negative news rather than neutral or
positive ones annoys us. A LOT. And it's gotten so bad that we are doing the only logical thing we, programmers, can do to 
help combat this: a bayesian classifier to help you get rid of those pesky sensationalist and tabloid articles, so you can enjoy
regular, fair news (altough sadly they become less regular being replaced by the aforementioned brain rot).

# Short rundown of our implementation
## What even is a ~~Bayer~~ Bayes classifier? 
In a nutshell, it uses previous observation and some statistical sugar to infer the probability of an event. Considering 
the apperence of a word in an article as a feature, and the apartenence to a certain class (either serious or tabloid or
sports, politics and diverse news) as the events we want to measure, we look at the distribution of our training data (we
aimed for 50/50 and kind of got it) and the probability of each word occuring in a certain class we can then use Bayes formula
with some ~~literally naive~~ clever assumptions to compute a prediction.
## How do we compute the final guesses?
Well we programmers are ~~stupid~~ lazy, and given that, we do not ~~know~~ care whether our features are independent, and we
just naively assume that they are, in our naive Bayes classifier (pun intended).

And so, to the best of our knowledge:

`P(A | B, C, D ...) = P(B | A, C | A, D | A ...) * P(A) / P(B, C, D ...)`

That means we can easily compute some inferences based on the Bayes formula, computing the probability of
finding our article in each of the classes, compare them and based on the highest one make a prediction about
the quality of our article.

The `naive_bayes_infer` function in the `classifier/main.py` file, we take precomputed probabilities of seeing each class 
in thw "wild" (the training data), and precomputed chances of finding each word in a certain class, then we use multithreading
to compute `multipliers`. We call a multiplier the numerator of the above fraction from the formula we used, and we only
compute those as the denominator is the same for the probability of beloning to each class, so we are only interested in how
those multipliers compare, not in the exact values, saving precious computation time.

After that, we get the maximum and see what class has it, or if there are multiple, what clasess have it, that meaning the 
result can equally belong to the classes listed. We print those nicely.

(we do our best but it's not easy to be a 🚀 programmer 🚀 🚀 🚀 🚀 🚀 🚀 🚀 🚀 ok one more 🚀)

## Erm, where'd you get all the data? Is it even legal?
We obviously are not news channels, as that would have helped tremendously in acquiring news articles text data. but we do
know some news websites, and some programming, so we wrote some scrapers (-> robots that ~~steal~~ get data from websites
for us). You can find the data we ~~stole~~ we acquired through (legal?) means in the `classifier/*.json` files (if you are
not familiar with globbing, that means all files with a .json extension).

Inside the `scraper/scraper` folder there are the spiders (the little robots that ~~steal~~ get data for us) and some boilerplate
configurations for `scapy` (the framework we used). The important (and written by us) bits, that are not part of the default 
config are in the `scraper/scraper/spiders` folder, each .py file representing the robot we wrote for a news website. We use xpath
to capture specific structures of each website that we observed manually and then read the text from there, classifying the
data as we gather it using some cues from the URLs (for example, we know that if the URL ends in `/stiri-politice` the news 
will be about politics, and so on). In the `classifier/main.py` file we run those multithreaded if the .jsons are missing, then run our
computations using numpy and some clever Python functions to quickly parse all those articles.

To wrap up this subsection about ~~stealing~~ data, we basically got 1773 articles, split about equally between tabloid 
(we considered Antena 3 and Wowbiz as tabloids, and Recorder and Pressone as serious sources), and separately split into
sports, politics and other news in a 14 to 51 to 34 -ish ratio.

We then took 100 of those as a test set and used the others for training data.

