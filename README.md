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
## How do we compute the final guesses?
Well we programmers are ~~stupid~~ lazy, and given that, we do not ~~know~~ care whether our features are independent, and we
just naively assume that they are, in our naive Bayes classifier (pun intended).

And so, to the best of our knowledge:

`P(A | B, C, D ...) = P(B | A, C | A, D | A ...) * P(A) / P(B, C, D ...)`

(we do our best but it's not easy to be a 🚀 programmer 🚀 🚀 🚀 🚀 🚀 🚀 🚀 🚀 ok one more 🚀)

# TODO