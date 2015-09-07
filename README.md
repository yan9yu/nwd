New Words Detection for Chinese
===============================

Detecting unlisting words, or new words for Chinese using Mutual Information and Max Entropy methods

### Algorithm
1. split the corpus and create n-gram tokens forwardly and backwardly
2. calculate the frequency of each token and drop tokens that appears rarely, eg. frequency=1
3. assume each token contains two words, calculate token mutual information, or cohesion by frequencies of the two words
4. calculate right most token's entropy for each token
5. filter results using frequency, cohesion and entropy limitations


### Reference

- [Mutual Information](https://en.wikipedia.org/wiki/Mutual_information)
- [互联网时代的社会语言学：基于SNS的文本数据挖掘](http://www.matrix67.com/blog/archives/5044)

