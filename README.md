
# Visual exploration

...of the positive integers when iterated with the Collatz conjecture transformations

## The Collatz conjecture

***Disclaimer**: This visualization is not an attempt to generate any result.*
*I haven't checked any proven or proposed results regarding the conjecture, mainly on purpose - I wanted to discover visual patterns in the collatz progression for myself.*
*Worst case - it looks pretty.*
*Best case - it could provide some visual insight (which, admittedly, would be useless without proper mathematical thinking and prior problem specific knowledge).*

  
  

[Collatz_conjecture @ Wikipedia](https://en.wikipedia.org/wiki/Collatz_conjecture)

  

Simplified (excerpt from Wikipedia):

* The conjecture asks whether repeating two simple arithmetic operations will eventually transform every positive integer into 1

* It concerns sequences of integers in which each term is obtained from the previous term as follows:

* If the previous term is even, the next term is one half of the previous term.

* If the previous term is odd, the next term is 3 times the previous term plus 1

* The conjecture is that these sequences always reach 1, no matter which positive integer is chosen to start the sequence.

  

## Concept of visualized data

Relevant properties of each number, in the context of the collatz iteration:

* If a *seed* number N1, iterated under collatz, reaches a number N2 and we know that N2 reaches 1, this means that N1 also reaches 1
* If the number N1 is a power of 2, the next numbers always follow the 'even' numbers case, which leads to 1, where it enters the 1-4-2-1 cycle
* We can define the sequence of numbers equal to powers of 2 as a special sequence - if a number, subjected to collatz iteration, ever reaches a power of 2, then it ends up in 1 (the 1-4-2-1 cycle)
* In this visualization the sequence of powers of 2 is called 'backbone'
* Consequently the powers of 2 are called vertebrae
* The length of the path a number takes to 1 differs, but part of that path always lies on the backbone. So the path can be split in two - before and along the backbone. Those are referred to as *full distance* and *distance to backbone*
* Closest vertebrae: The first power of 2 that an iteration reaches
* Peak: The maximum number that a progression of a particular *seed* number reaches
* Peak slope: The ratio of a *seed* number's peek to the number itself
* Bound: a boolean property denoting whether the peak of a given *seed* number is higher than the maximum number for which a plot is generated (*plot limit*). For each plot limit, the ratio of bound numbers to all included numbers appears to be approximately constant
* Odd parent: Under collatz iteration, an arbitrary number can be pottentially reached in one of two ways - from a preceding even number Ne (Ne / 2) or from a preceding odd number No (No * 3 + 1). Ne and No are referred to as parents. All numbers have an even parent, but not all have an odd parent. The ratio of numbers having an odd parent can be explored via the 'odd parent' boolean property


***Example: distance to backbone***

If the starting number is 10, the full path is 10, 5, 16, 8, 4, 2, 1

The first power of 2 in the path is 16, so the *distance to backbone* of 10 is 1 (10 itself is excluded, which leaves *5*)

Grouping numbers by their *distance to backbone* equates, for example, 80 and 13, as they both have a *distance to backbone* of 4:

* 80 >> 80, 40, 20, 10, 5, *16, 8, 4, 2, 1*

* 13 >> 13, 40, 20, 10, 5, *16, 8, 4, 2, 1*

***Example: properties***
- value: **37**
- is a vertebrae (power of 2): False
- ful path: [112, 56, 28, 14, 7, 22, 11, 34, 17, 52, 26, 13, 40, 20, 10, 5, 16, 8, 4, 2, 1]
- full distance to 1: 21
- distance to bb: 17
- closest vertebrae value: 16
- closest vertebrae power: 4
- peak: 112
- peak slope: 3.027027027027027
- odd parent: False
- bounded: False

* When plotting, the backbone numbers are excluded by default, as their properties do not offer any significant insight and their patterns are trivial.

* Due to the fact that full paths are included in the data, generating a data file gets exponentially slower for larger datasets.
    * The size of the data file also may present a problem. One hundred thousand datapoints result in 56Mb db file, while the 1 mln file is about 916 Mb. The html plot file also scales significantly with dataset size.
    * For this reason the full the largest dataset files can not be trivially stored in the repo. Other solutions will be explored for sharing the pre-generated data.

## How to view the html

The main html file (the latest generated) can be viewed by opening the following link:
https://raw.githack.com/MossGoblin/collatz_plot/master/main.html
* *Note*: The main.html file is the lates that I have generated locally. Means for viewing any stashed html files (with notable plots) will be added later.

## TODO
- [ ] An advanced filtering agent is needed for easily modifying the plotted data.
