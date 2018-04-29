import numpy as np
import pandas as pd
import os
from os import listdir
from os.path import isfile, join
# website stuff
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField, SelectMultipleField, RadioField, widgets
from wtforms.validators import Required
import re

################################################## words, dictionary

class Word:
    def __init__(self, word, POS, specials,
                 use = None, usei = None, cat = None):
        # word = the word (a lowercase string)
        # POS = the part of speech (an uppercase string)
        # specials = the list of satisfied demands (a list of uppercase strings)
        #   specials should include
        #       - all general demands specific to the part of speech
        #       - compound
        #       - third player demands for verbs/adverbs/conjunctions
        # use = an example of the word being used (a string without a period)
        #   only auxiliary verbs and pronouns should have a non-None use
        # cat = the category of the word (an uppercase string)
        #   only non-auxiliary verbs should have a non-None category
        self.word = word
        self.POS = POS
        self.specials = specials
        self.use = use
        self.usei = usei
        self.cat = cat

DICTIONARY = []

def verb_category_to_demands(c):
    # input: category c
    if c == "PRESENT_I":
        return ["SINGULAR","SIMPLE","SIMPLEPRESENT"]
    if c == "PRESENT_HE":
        return ["SINGULAR","SIMPLE","SIMPLEPRESENT"]
    if c == "PRESENT_THEY":
        return ["PLURAL","SIMPLE","SIMPLEPRESENT"]
    if c == "PAST_I":
        return ["SINGULAR","SIMPLE","SIMPLEPAST"]
    if c == "PAST_THEY":
        return ["PLURAL","SIMPLE","SIMPLEPAST"]
    if c == "FUTURE":
        return ["SINGULAR","PLURAL","SIMPLE","SIMPLEFUTURE"]
    L = ["","PAST","PRESENT","FUTURE"]
    if c == "PERFECT":
        newL = ["PERFECT" + x for x in L]
        return ["SINGULAR","PLURAL"] + newL
    if c == "PROGRESSIVE":
        newL1 = ["PROGRESSIVE" + x for x in L]
        newL2 = ["PERFECTPROGRESSIVE" + x for x in L]
        return ["SINGULAR","PLURAL"] + newL1 + newL2
    if c in ["SIMPLE","GERUND","PRESENT_PARTICIPLE","PAST_PARTICIPLE"]:
        return c
    return []

def verb_get_suffix(w):
    
    # input: Word w with w.POS == "VERB" and "MAINVERB" in w.specials
    
    def verb_get_used_tense(D):
        L1 = ["PAST","PERFECT","FUTURE"]
        L2 = ["SIMPLE","PERFECT","PROGRESSIVE","PERFECTPROGRESSIVE"]
        X = [d for d in D if d not in ["SINGULAR","PLURAL"] + L2]
        for g in L2:
            if g in GENERALS:
                X = [x for x in X if x in [g+l for l in L1]]
        for g in GENERALS:
            if g in X:
                return g
        return X[0]

    t_i_l = "LINKING" if "LINKING" in w.specials else ("INTRANSITIVE" if "INTRANSITIVE" in w.specials else "TRANSITIVE")
    if "INFINITIVE" in w.specials:
        for g in GENERALS:
            if g[0] == ":":
                return "_INFINITIVE_" + g[1:]
        L2 = ["SIMPLE","PERFECT","PROGRESSIVE","PERFECTPROGRESSIVE"]
        for g in L2:
            if g in GENERALS:
                return "_INFINITIVE_" + g + "_" + t_i_l
        return "_INFINITIVE_" + w.cat + "_" + t_i_l
    if "GERUND" in w.specials:
        for g in GENERALS:
            if g[0] == ":":
                return "_GERUND_" + g[1:]
        return "_GERUND_" + t_i_l
    if "PARTICIPLE" in w.specials:
        return "_PARTICIPLE_" + t_i_l
    satisfied_demands = verb_category_to_demands(w.cat)
    s_p = "SINGULAR"
    if "PLURAL" in GENERALS or "SINGULAR" not in satisfied_demands:
        s_p = "PLURAL"
    if s_p == "SINGULAR" and w.cat == "PRESENT_HE":
        s_p = "SINGULAR_HE"
    tense = verb_get_used_tense(satisfied_demands)
    return "_MAINVERB_" + tense + "_" + t_i_l + "_" + s_p

def initialize_dictionary_verb(df):
    # input: data frame df
    words = np.array(df["VERB"])
    for i in range(len(words)):
        if df["TYPE"][i] == "AUXILIARY":
            S = ["AUXILIARY"]
            use = df["USE"][i]
            usei = df["USEI"][i] if isinstance(df["USEI"][i], str) else None
            DICTIONARY.append(Word(words[i], "VERB", S, use = use, usei = usei))
        elif df["TYPE"][i] == "MAINVERB":
            S = ["MAINVERB", df["R/I"][i]]
            if not np.isnan(df["COMPOUND"][i]):
                S.append("COMPOUND")
            for s in df["T/I/L"][i].split("/"):
                S.append(s)
            for c in ["PRESENT_I","PRESENT_HE","PRESENT_THEY","PAST_I",
                      "PAST_THEY","FUTURE","PERFECT","PROGRESSIVE"]:
                DICTIONARY.append(Word(df[c][i], "VERB", S, cat = c))
            T = [s for s in S]
            T[0] = "INFINITIVE"
            T.append("VERBAL")
            DICTIONARY.append(Word(words[i], "VERB", T, cat = "SIMPLE"))
            for c in ["PERFECT","PROGRESSIVE"]:
                DICTIONARY.append(Word(df[c][i], "VERB", T, cat = c))
            U = [t for t in T]
            U[0] = "GERUND"
            DICTIONARY.append(Word(df["PROGRESSIVE"][i], "VERB", U,
                                   cat = "GERUND"))
            V = [u for u in U]
            V[0] = "PARTICIPLE"
            DICTIONARY.append(Word(df["PROGRESSIVE"][i], "VERB", V,
                                   cat = "PRESENT_PARTICIPLE"))
            if not np.isnan(df["PAST_PARTICIPLE"][i]):
                W = [v for v in V]
                W[0] = "PARTICIPLE"
                DICTIONARY.append(Word(df["PERFECT"][i], "VERB", W,
                                       cat = "PAST_PARTICIPLE"))

def initialize_dictionary(P2):
    # input: player two demand P2
    mypath = "WordLists"
    onlyfiles = [join(mypath, f) for f in listdir(mypath) if f.endswith(".csv")]
    for f in onlyfiles:
        df = pd.read_csv(f)
        if P2 == df.keys()[0]:
            if P2 == "VERB":
                initialize_dictionary_verb(df)
            else:
                words = np.array(df[P2])
                Q = np.array(df.keys())[1:]
                for i in range(len(words)):
                    S = [x for x in Q if not np.isnan(df[x][i])]
                    DICTIONARY.append(Word(words[i], P2, S))

def string_can_be_made_with_cubes(s):
    # input: lowercase string s
    if LETTER_TRANSFER[0]:
        if LETTER_TRANSFER[0] in s:
            return False
    num_wild_cubes = 0
    if COLOR_WILD:
        num_wild_cubes = len(CUBES[COLOR_WILD])
    non_wild_cubes = ""
    for color in CUBES.keys():
        if color != COLOR_WILD:
            non_wild_cubes += CUBES[color]
    if LETTER_TRANSFER[0]:
        for i in range(len(non_wild_cubes)):
            if non_wild_cubes[i] == LETTER_TRANSFER[0]:
                non_wild_cubes[i] = LETTER_TRANSFER[1]
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    s_counts = [s.count(c) for c in alphabet]
    non_wild_cubes_counts = [non_wild_cubes.count(c) for c in alphabet]
    num_wild_cubes_needed = 0
    for i in range(len(alphabet)):
        if s_counts[i] > non_wild_cubes_counts[i]:
            num_wild_cubes_needed += s_counts[i] - non_wild_cubes_counts[i]
    return (num_wild_cubes_needed <= num_wild_cubes)

def word_is_valid(w, P1, P2, P3):
    # input: Word w, player one demand P1, player two demand P2, player three demand P3
    if w.POS != P2:
        return False
    if len(w.word) < 4 or len(w.word) > 10:
        return False
    if NUMBER_OF_LETTERS:
        if len(w.word) != NUMBER_OF_LETTERS:
            return False
    if DOUBLE_VOWEL:
        dv = False
        vowels = "aeiouy"
        for i in range(len(w.word)-1):
            if w.word[i] in vowels and w.word[i] == w.word[i+1]:
                dv = True
                break
        if not dv:
            return False
    if DOUBLE_CONSONANT:
        dc = False
        consonants = "bcdfghjklmnpqrstvwxyz"
        for i in range(len(w.word)-1):
            if w.word[i] in consonants and w.word[i] == w.word[i+1]:
                dc = True
                break
        if not dc:
            return False
    if MUST_CONTAIN:
        if MUST_CONTAIN not in w.word:
            return False
    if MUST_NOT_CONTAIN:
        if MUST_NOT_CONTAIN in w.word:
            return False
    if LETTER_TRANSFER[0]:
        if LETTER_TRANSFER[0] in w.word:
            return False
    if w.POS in ["VERB","ADVERB","CONJUNCTION"]:
        if P3 and P3 not in w.specials:
            return False
    for g in GENERALS:
        if g not in w.specials:
            if P2 == "VERB" and g[0] == ":":
                if "INTRANSITIVE" not in w.specials:
                    return False
                if w.cat != "SIMPLE" and w.cat != "GERUND":
                    return False
            elif P2 == "VERB" and P3 != "AUXILIARY":
                if g not in verb_category_to_demands(w.cat):
                    return False
            else:
                return False
    if USE_CUBES:
        if not string_can_be_made_with_cubes(w.word):
            return False
    if P3 == "AUXILIARY" and w.usei is None:
        if P1 in ["SIMPLE","COMPOUND"] and PHRASES != ():
            return False
    if P2 == "PRONOUN":
        if P3 not in ["SUBJECT","PREDICATENOUN","APPOSITIVE"]:
            if "OBJECTIVECASE" not in w.specials:
                return False
        if P1 in ["SIMPLE","COMPOUND"] and PHRASES != ():
            if "INTERROGATIVE" in w.specials or "RELATIVE" in w.specials:
                return False
        if P3 == "APPOSITIVE":
            if "INTERROGATIVE" in w.specials or "RELATIVE" in w.specials:
                return False
    return True

################################################## sentence building blocks

########## Basic/Simple Sentence Fragmets

BASIC_SENTENCE_FRAGMENTS = dict()
SIMPLE_SENTENCE_FRAGMENTS = dict()

##### No Clauses, No Phrases

BASIC_SENTENCE_FRAGMENTS[((),())] = "because saying, \"{0},\" is bad"

##### No Clause, One Phrase

BASIC_SENTENCE_FRAGMENTS[((),("APPOSITIVE",))] = "because they, people saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[((),("INFINITIVE",))] = "because wanting to say, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[((),("GERUND",))] = "because saying, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[((),("PARTICIPIAL",))] = "because people saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[((),("PREPOSITIONAL",))] = "because books about saying, \"{0},\" are bad"
BASIC_SENTENCE_FRAGMENTS[((),("ADJECTIVE",))] = "because books about saying, \"{0},\" are bad"
BASIC_SENTENCE_FRAGMENTS[((),("ADVERB",))] = "because writing about saying, \"{0},\" is bad"

SIMPLE_SENTENCE_FRAGMENTS[((),("APPOSITIVE",))] = "They, people wanting to {0}, ran"
SIMPLE_SENTENCE_FRAGMENTS[((),("INFINITIVE",))] = "People wanting to {0} ran"
SIMPLE_SENTENCE_FRAGMENTS[((),("GERUND",))] = "Wanting to {0} is bad"
SIMPLE_SENTENCE_FRAGMENTS[((),("PARTICIPIAL",))] = "People wanting to {0} ran"
SIMPLE_SENTENCE_FRAGMENTS[((),("PREPOSITIONAL",))] = "Writing about wanting to {0} is bad"
SIMPLE_SENTENCE_FRAGMENTS[((),("ADJECTIVE",))] = "Books about wanting to {0} are bad"
SIMPLE_SENTENCE_FRAGMENTS[((),("ADVERB",))] = "Writing about wanting to {0} is bad"

##### No Clauses, Two Phrases

BASIC_SENTENCE_FRAGMENTS[((),("APPOSITIVE","INFINITIVE"))] = "because they, people wanting to say, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[((),("APPOSITIVE","GERUND"))] = "because they, people considering saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[((),("APPOSITIVE","PARTICIPIAL"))] = "because they, people saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[((),("APPOSITIVE","PREPOSITIONAL"))] = "because they, people thinking about saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[((),("APPOSITIVE","ADJECTIVE"))] = "because they, books about saying, \"{0},\" are bad"
BASIC_SENTENCE_FRAGMENTS[((),("APPOSITIVE","ADVERB"))] = "because they, people thinking about saying, \"{0},\" ran"

BASIC_SENTENCE_FRAGMENTS[((),("INFINITIVE","GERUND"))] = "because wanting to say, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[((),("INFINITIVE","PARTICIPIAL"))] = "because people wanting to say, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[((),("INFINITIVE","PREPOSITIONAL"))] = "because thinking about wanting to say, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[((),("INFINITIVE","ADJECTIVE"))] = "because books about wanting to say, \"{0},\" are bad"
BASIC_SENTENCE_FRAGMENTS[((),("INFINITIVE","ADVERB"))] = "because thinking about wanting to say, \"{0},\" is bad"

BASIC_SENTENCE_FRAGMENTS[((),("GERUND","PARTICIPIAL"))] = "because people considering saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[((),("GERUND","PREPOSITIONAL"))] = "because thinking about saying, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[((),("GERUND","ADJECTIVE"))] = "because books about saying, \"{0},\" are bad"
BASIC_SENTENCE_FRAGMENTS[((),("GERUND","ADVERB"))] = "because thinking about saying, \"{0},\" is bad"

BASIC_SENTENCE_FRAGMENTS[((),("PARTICIPIAL","PREPOSITIONAL"))] = "because people thinking about saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[((),("PARTICIPIAL","ADJECTIVE"))] = "because people writing books about saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[((),("PARTICIPIAL","ADVERB"))] = "because people thinking about saying, \"{0},\" ran"

BASIC_SENTENCE_FRAGMENTS[((),("PREPOSITIONAL","ADJECTIVE"))] = BASIC_SENTENCE_FRAGMENTS[((),("ADJECTIVE",))]
BASIC_SENTENCE_FRAGMENTS[((),("PREPOSITIONAL","ADVERB"))] = BASIC_SENTENCE_FRAGMENTS[((),("ADVERB",))]

BASIC_SENTENCE_FRAGMENTS[((),("ADJECTIVE","ADVERB"))] = "because thinking about writing books about saying, \"{0},\" is bad"

SIMPLE_SENTENCE_FRAGMENTS[((),("APPOSITIVE","INFINITIVE"))] = SIMPLE_SENTENCE_FRAGMENTS[((),("APPOSITIVE",))]
SIMPLE_SENTENCE_FRAGMENTS[((),("APPOSITIVE","GERUND"))] = "They, people considering wanting to {0}, ran"
SIMPLE_SENTENCE_FRAGMENTS[((),("APPOSITIVE","PARTICIPIAL"))] = "They, people wanting to {0}, ran"
SIMPLE_SENTENCE_FRAGMENTS[((),("APPOSITIVE","PREPOSITIONAL"))] = "They, books about wanting to {0}, are bad"
SIMPLE_SENTENCE_FRAGMENTS[((),("APPOSITIVE","ADJECTIVE"))] = "They, books about wanting to {0}, are bad"
SIMPLE_SENTENCE_FRAGMENTS[((),("APPOSITIVE","ADVERB"))] = "They, people thinking about wanting to {0}, ran"

SIMPLE_SENTENCE_FRAGMENTS[((),("INFINITIVE","GERUND"))] = SIMPLE_SENTENCE_FRAGMENTS[((),("GERUND",))]
SIMPLE_SENTENCE_FRAGMENTS[((),("INFINITIVE","PARTICIPIAL"))] = SIMPLE_SENTENCE_FRAGMENTS[((),("PARTICIPIAL",))]
SIMPLE_SENTENCE_FRAGMENTS[((),("INFINITIVE","PREPOSITIONAL"))] = SIMPLE_SENTENCE_FRAGMENTS[((),("PREPOSITIONAL",))]
SIMPLE_SENTENCE_FRAGMENTS[((),("INFINITIVE","ADJECTIVE"))] = SIMPLE_SENTENCE_FRAGMENTS[((),("ADJECTIVE",))]
SIMPLE_SENTENCE_FRAGMENTS[((),("INFINITIVE","ADVERB"))] = SIMPLE_SENTENCE_FRAGMENTS[((),("ADVERB",))]

SIMPLE_SENTENCE_FRAGMENTS[((),("GERUND","PARTICIPIAL"))] = "People considering wanting to {0} ran"
SIMPLE_SENTENCE_FRAGMENTS[((),("GERUND","PREPOSITIONAL"))] = "Thinking about wanting to {0} is bad"
SIMPLE_SENTENCE_FRAGMENTS[((),("GERUND","ADJECTIVE"))] = "Books about wanting to {0} are bad"
SIMPLE_SENTENCE_FRAGMENTS[((),("GERUND","ADVERB"))] = "Thinking about wanting to {0} is bad"

SIMPLE_SENTENCE_FRAGMENTS[((),("PARTICIPIAL","PREPOSITIONAL"))] = "People thinking about wanting to {0} ran"
SIMPLE_SENTENCE_FRAGMENTS[((),("PARTICIPIAL","ADJECTIVE"))] = "People writing books about wanting to {0} ran"
SIMPLE_SENTENCE_FRAGMENTS[((),("PARTICIPIAL","ADVERB"))] = "People thinking about wanting to {0} ran"

SIMPLE_SENTENCE_FRAGMENTS[((),("PREPOSITIONAL","ADJECTIVE"))] = SIMPLE_SENTENCE_FRAGMENTS[((),("ADJECTIVE",))]
SIMPLE_SENTENCE_FRAGMENTS[((),("PREPOSITIONAL","ADVERB"))] = SIMPLE_SENTENCE_FRAGMENTS[((),("ADVERB",))]

SIMPLE_SENTENCE_FRAGMENTS[((),("ADJECTIVE","ADVERB"))] = "Thinking about writing books about wanting to {0} is bad"

##### One Clause, No Phrases

BASIC_SENTENCE_FRAGMENTS[(("DEPENDENT",),())] = "because saying, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[(("ADJECTIVE",),())] = "because people who said, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[(("ADVERB",),())] = "because saying, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[(("NOUN",),())] = "because saying, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[(("INFINITIVE",),())] = "because wanting him to say, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[(("KRINGLE",),())] = BASIC_SENTENCE_FRAGMENTS[(("DEPENDENT",),())] + " on Christmas"

##### One Clause, One Phrase

BASIC_SENTENCE_FRAGMENTS[(("DEPENDENT",),("APPOSITIVE",))] = "because they, people saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[(("DEPENDENT",),("INFINITIVE",))] = "because wanting to say, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[(("DEPENDENT",),("GERUND",))] = "because saying, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[(("DEPENDENT",),("PARTICIPIAL",))] = "because people saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[(("DEPENDENT",),("PREPOSITIONAL",))] = "because books about saying, \"{0},\" are bad"
BASIC_SENTENCE_FRAGMENTS[(("DEPENDENT",),("ADJECTIVE",))] = "because books about saying, \"{0},\" are bad"
BASIC_SENTENCE_FRAGMENTS[(("DEPENDENT",),("ADVERB",))] = "because writing about saying, \"{0},\" is bad"

BASIC_SENTENCE_FRAGMENTS[(("ADJECTIVE",),("APPOSITIVE",))] = "because they, people who said, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[(("ADJECTIVE",),("INFINITIVE",))] = "because people who want to say, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[(("ADJECTIVE",),("GERUND",))] = "because people who considered saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[(("ADJECTIVE",),("PARTICIPIAL",))] = "because people who considered people saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[(("ADJECTIVE",),("PREPOSITIONAL",))] = "because people who thought about saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[(("ADJECTIVE",),("ADJECTIVE",))] = "because people who wrote books about saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[(("ADJECTIVE",),("ADVERB",))] = "because people who thought about saying, \"{0},\" ran"

BASIC_SENTENCE_FRAGMENTS[(("ADVERB",),("APPOSITIVE",))] = "because they, people saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[(("ADVERB",),("INFINITIVE",))] = "because wanting to say, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[(("ADVERB",),("GERUND",))] = "because saying, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[(("ADVERB",),("PARTICIPIAL",))] = "because people saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[(("ADVERB",),("PREPOSITIONAL",))] = "because books about saying, \"{0},\" are bad"
BASIC_SENTENCE_FRAGMENTS[(("ADVERB",),("ADJECTIVE",))] = "because books about saying, \"{0},\" are bad"
BASIC_SENTENCE_FRAGMENTS[(("ADVERB",),("ADVERB",))] = "because writing about saying, \"{0},\" is bad"

BASIC_SENTENCE_FRAGMENTS[(("NOUN",),("APPOSITIVE",))] = "because they, people saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[(("NOUN",),("INFINITIVE",))] = "because wanting to say, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[(("NOUN",),("GERUND",))] = "because saying, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[(("NOUN",),("PARTICIPIAL",))] = "because people saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[(("NOUN",),("PREPOSITIONAL",))] = "because books about saying, \"{0},\" are bad"
BASIC_SENTENCE_FRAGMENTS[(("NOUN",),("ADJECTIVE",))] = "because books about saying, \"{0},\" are bad"
BASIC_SENTENCE_FRAGMENTS[(("NOUN",),("ADVERB",))] = "because writing about saying, \"{0},\" is bad"

BASIC_SENTENCE_FRAGMENTS[(("INFINITIVE",),("APPOSITIVE",))] = "because they, people wanting him to say, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[(("INFINITIVE",),("INFINITIVE",))] = "because wanting him to want to say, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[(("INFINITIVE",),("GERUND",))] = "because wanting him to say, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[(("INFINITIVE",),("PARTICIPIAL",))] = "because people wanting him to say, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[(("INFINITIVE",),("PREPOSITIONAL",))] = "because wanting him to think about saying, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[(("INFINITIVE",),("ADJECTIVE",))] = "because wanting him to write books about saying, \"{0},\" is bad"
BASIC_SENTENCE_FRAGMENTS[(("INFINITIVE",),("ADVERB",))] = "because wanting him to think about saying, \"{0},\" is bad"

BASIC_SENTENCE_FRAGMENTS[(("KRINGLE",),("APPOSITIVE",))] = BASIC_SENTENCE_FRAGMENTS[((),("APPOSITIVE",))] + " on Christmas"
BASIC_SENTENCE_FRAGMENTS[(("KRINGLE",),("INFINITIVE",))] = BASIC_SENTENCE_FRAGMENTS[((),("INFINITIVE",))] + " on Christmas"
BASIC_SENTENCE_FRAGMENTS[(("KRINGLE",),("GERUND",))] = BASIC_SENTENCE_FRAGMENTS[((),("GERUND",))] + " on Christmas"
BASIC_SENTENCE_FRAGMENTS[(("KRINGLE",),("PARTICIPIAL",))] = BASIC_SENTENCE_FRAGMENTS[((),("PARTICIPIAL",))] + " on Christmas"
BASIC_SENTENCE_FRAGMENTS[(("KRINGLE",),("PREPOSITIONAL",))] = BASIC_SENTENCE_FRAGMENTS[((),("PREPOSITIONAL",))] + " on Christmas"
BASIC_SENTENCE_FRAGMENTS[(("KRINGLE",),("ADJECTIVE",))] = BASIC_SENTENCE_FRAGMENTS[((),("ADJECTIVE",))] + " on Christmas"
BASIC_SENTENCE_FRAGMENTS[(("KRINGLE",),("ADVERB",))] = BASIC_SENTENCE_FRAGMENTS[((),("ADVERB",))] + " on Christmas"

##### Two Clauses, No Phrases

BASIC_SENTENCE_FRAGMENTS[(("DEPENDENT","ADJECTIVE"),())] = BASIC_SENTENCE_FRAGMENTS[(("ADJECTIVE",),())]
BASIC_SENTENCE_FRAGMENTS[(("DEPENDENT","ADVERB"),())] = BASIC_SENTENCE_FRAGMENTS[(("ADVERB",),())]
BASIC_SENTENCE_FRAGMENTS[(("DEPENDENT","NOUN"),())] = BASIC_SENTENCE_FRAGMENTS[(("NOUN",),())]
BASIC_SENTENCE_FRAGMENTS[(("DEPENDENT","INFINITIVE"),())] = BASIC_SENTENCE_FRAGMENTS[(("INFINITIVE",),())]

BASIC_SENTENCE_FRAGMENTS[(("ADJECTIVE","ADVERB"),())] = "because people who said, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[(("ADJECTIVE","NOUN"),())] = "because people who said, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[(("ADJECTIVE","INFINITIVE"),())] = "because people who want him to say, \"{0},\" ran"

BASIC_SENTENCE_FRAGMENTS[(("ADVERB","NOUN"),())] = "because people saying, \"{0},\" ran"
BASIC_SENTENCE_FRAGMENTS[(("ADVERB","INFINITIVE"),())] = "because wanting him to say, \"{0},\" is bad"

BASIC_SENTENCE_FRAGMENTS[(("NOUN","INFINITIVE"),())] = BASIC_SENTENCE_FRAGMENTS[(("INFINITIVE",),())]

BASIC_SENTENCE_FRAGMENTS[(("KRINGLE","DEPENDENT"),())] = BASIC_SENTENCE_FRAGMENTS[(("DEPENDENT",),())] + " on Christmas"
BASIC_SENTENCE_FRAGMENTS[(("KRINGLE","ADJECTIVE"),())] = BASIC_SENTENCE_FRAGMENTS[(("ADJECTIVE",),())] + " on Christmas"
BASIC_SENTENCE_FRAGMENTS[(("KRINGLE","ADVERB"),())] = BASIC_SENTENCE_FRAGMENTS[(("ADVERB",),())] + " on Christmas"
BASIC_SENTENCE_FRAGMENTS[(("KRINGLE","NOUN"),())] = BASIC_SENTENCE_FRAGMENTS[(("NOUN",),())] + " on Christmas"
BASIC_SENTENCE_FRAGMENTS[(("KRINGLE","INFINITIVE"),())] = BASIC_SENTENCE_FRAGMENTS[(("INFINITIVE",),())] + " on Christmas"

########## Sentences

SENTENCES = dict()

SENTENCES["SIMPLE"] = "{0}."
SENTENCES["COMPOUND"] = "{0} and I ran."
SENTENCES["COMPLEX"] = "I ran {0}."
SENTENCES["COMPOUNDCOMPLEX"] = "I ran and he ran {0}."

SENTENCES["DECLARATIVE"] = "I ran {0}."
SENTENCES["INTERROGATIVE"] = "Did he run {0}?"
SENTENCES["IMPERATIVE"] = "Run {0}"
SENTENCES["EXCLAMATORY"] = "I ran {0}!"

SENTENCES["SV"] = "I ran {0}."
SENTENCES["SVDO"] = "I hit it {0}."
SENTENCES["SVIODO"] = "I gave him gifts {0}."
SENTENCES["SLVPN"] = "It is it {0}."
SENTENCES["SLVPA"] = "I am old {0}."
SENTENCES["SVDOOC(N)"] = "I called them people {0}."
SENTENCES["SVDOOC(A)"] = "I called them cool {0}."
SENTENCES["INVERTED"] = "Here is he {0}."

########## Fragments

FRAGMENTS = dict()
SIMPLE_FRAGMENTS = dict()

##### Noun Fragments

FRAGMENTS["NOUN_SUBJECT"] = "The {0} worked"
FRAGMENTS["NOUN_DIRECTOBJECT"] = "I considered the {0}"
FRAGMENTS["NOUN_INDIRECTOBJECT"] = "I gave the {0} consideration"
FRAGMENTS["NOUN_PREDICATENOUN"] = "The reason is the {0}"
FRAGMENTS["NOUN_OBJECTOFPREPOSITION"] = "I thought about the {0}"
FRAGMENTS["NOUN_APPOSITIVE"] = "The reason, the {0}, worked"
FRAGMENTS["NOUN_NOUNUSEDASADJECTIVE"] = "The {0} considerer worked"
FRAGMENTS["NOUN_OBJECTIVECOMPLEMENT"] = "I called the reason the {0}"
FRAGMENTS["NOUN_SUBJECT_OBJECTIVECASE"] = "I want the {0} to work"
FRAGMENTS["NOUN_PREDICATENOUN_OBJECTIVECASE"] = "I want it to be the {0}"
FRAGMENTS["NOUN_APPOSITIVE_OBJECTIVECASE"] = "I considered the reason, the {0}"

SIMPLE_FRAGMENTS["NOUN_SUBJECT"] = "The {0} worked"
SIMPLE_FRAGMENTS["NOUN_DIRECTOBJECT"] = "consider the {0}"
SIMPLE_FRAGMENTS["NOUN_INDIRECTOBJECT"] = "give the {0} consideration"
SIMPLE_FRAGMENTS["NOUN_PREDICATENOUN"] = "be the {0}"
SIMPLE_FRAGMENTS["NOUN_OBJECTOFPREPOSITION"] = "think about the {0}"
SIMPLE_FRAGMENTS["NOUN_APPOSITIVE"] = "be the reason, the {0},"
SIMPLE_FRAGMENTS["NOUN_NOUNUSEDASADJECTIVE"] = "consider the {0} considerer"
SIMPLE_FRAGMENTS["NOUN_APPOSITIVE_OBJECTIVECASE"] = "consider the reason, the {0},"

##### Pronoun Fragments

# demonstrative, indefinite, possessive personal

FRAGMENTS["PRONOUN_SUBJECT"] = "Happily {0} worked"
FRAGMENTS["PRONOUN_DIRECTOBJECT"] = "I considered {0}"
FRAGMENTS["PRONOUN_INDIRECTOBJECT"] = "I gave {0} consideration"
FRAGMENTS["PRONOUN_PREDICATENOUN"] = "The reason is {0}"
FRAGMENTS["PRONOUN_OBJECTOFPREPOSITION"] = "I thought about {0}"
FRAGMENTS["PRONOUN_APPOSITIVE"] = "The reason, {0}, worked"
FRAGMENTS["PRONOUN_OBJECTIVECOMPLEMENT"] = "I called the reason {0}"
FRAGMENTS["PRONOUN_SUBJECT_OBJECTIVECASE"] = "I want {0} to work"
FRAGMENTS["PRONOUN_PREDICATENOUN_OBJECTIVECASE"] = "I want it to be {0}"
FRAGMENTS["PRONOUN_APPOSITIVE_OBJECTIVECASE"] = "I considered the reason, {0}"

SIMPLE_FRAGMENTS["PRONOUN_SUBJECT"] = "Happily {0} worked"
SIMPLE_FRAGMENTS["PRONOUN_DIRECTOBJECT"] = "consider {0}"
SIMPLE_FRAGMENTS["PRONOUN_INDIRECTOBJECT"] = "give {0} consideration"
SIMPLE_FRAGMENTS["PRONOUN_PREDICATENOUN"] = "be {0}"
SIMPLE_FRAGMENTS["PRONOUN_OBJECTOFPREPOSITION"] = "think about {0}"
SIMPLE_FRAGMENTS["PRONOUN_APPOSITIVE"] = "be the reason, {0},"
SIMPLE_FRAGMENTS["PRONOUN_APPOSITIVE_OBJECTIVECASE"] = "consider the reason, {0},"

# interrogative

FRAGMENTS["INTERROGATIVE_PRONOUN_SUBJECT_NOMINATIVECASE"] = "Now, {0} worked?"
FRAGMENTS["INTERROGATIVE_PRONOUN_DIRECTOBJECT_OBJECTIVECASE"] = "Now, {0} did you consider?"
FRAGMENTS["INTERROGATIVE_PRONOUN_INDIRECTOBJECT_OBJECTIVECASE"] = "Now, {0} did you give consideration?"
FRAGMENTS["INTERROGATIVE_PRONOUN_PREDICATENOUN_NOMINATIVECASE"] = "Now, {0} did the reason use to be?"
FRAGMENTS["INTERROGATIVE_PRONOUN_OBJECTOFPREPOSITION_OBJECTIVECASE"] = "About {0} did you think?"
FRAGMENTS["INTERROGATIVE_PRONOUN_OBJECTIVECOMPLEMENT_OBJECTIVECASE"] = "Now, {0} did you call it?"
FRAGMENTS["INTERROGATIVE_PRONOUN_SUBJECT_OBJECTIVECASE"] = "Now, {0} did you want to be the reason?"
FRAGMENTS["INTERROGATIVE_PRONOUN_PREDICATENOUN_OBJECTIVECASE"] = "Now, {0} did you want the reason to be?"

# relative

FRAGMENTS["RELATIVE_PRONOUN_SUBJECT_NOMINATIVECASE"] = "I considered those {0} worked"
FRAGMENTS["RELATIVE_PRONOUN_DIRECTOBJECT_OBJECTIVECASE"] = "I considered those {0} I considered"
FRAGMENTS["RELATIVE_PRONOUN_INDIRECTOBJECT_OBJECTIVECASE"] = "I considered those {0} I gave consideration"
FRAGMENTS["RELATIVE_PRONOUN_PREDICATENOUN_NOMINATIVECASE"] = "I considered those {0} the reason is"
FRAGMENTS["RELATIVE_PRONOUN_OBJECTOFPREPOSITION_OBJECTIVECASE"] = "I considered those about {0} I thought"
FRAGMENTS["RELATIVE_PRONOUN_OBJECTIVECOMPLEMENT_OBJECTIVECASE"] = "I considered those {0} I called the reason"
FRAGMENTS["RELATIVE_PRONOUN_SUBJECT_OBJECTIVECASE"] = "I considered those {0} I want to work"
FRAGMENTS["RELATIVE_PRONOUN_PREDICATENOUN_OBJECTIVECASE"] = "I considered those {0} I want it to be"

FRAGMENTS["FREE_RELATIVE_PRONOUN_SUBJECT_NOMINATIVECASE"] = "I considered {0} worked"
FRAGMENTS["FREE_RELATIVE_PRONOUN_DIRECTOBJECT_OBJECTIVECASE"] = "I considered {0} I considered"
FRAGMENTS["FREE_RELATIVE_PRONOUN_INDIRECTOBJECT_OBJECTIVECASE"] = "I considered {0} I gave consideration"
FRAGMENTS["FREE_RELATIVE_PRONOUN_PREDICATENOUN_NOMINATIVECASE"] = "I considered {0} the reason is"
FRAGMENTS["FREE_RELATIVE_PRONOUN_OBJECTOFPREPOSITION_OBJECTIVECASE"] = "I considered about {0} I thought"
FRAGMENTS["FREE_RELATIVE_PRONOUN_OBJECTIVECOMPLEMENT_OBJECTIVECASE"] = "I considered {0} I called the reason"
FRAGMENTS["FREE_RELATIVE_PRONOUN_SUBJECT_OBJECTIVECASE"] = "I considered {0} I want to work"
FRAGMENTS["FREE_RELATIVE_PRONOUN_PREDICATENOUN_OBJECTIVECASE"] = "I considered {0} I want it to be"

# non-posessive personal

FRAGMENTS["PERSONAL_PRONOUN_SUBJECT_NOMINATIVECASE"] = "Happily {0} worked"
FRAGMENTS["PERSONAL_PRONOUN_DIRECTOBJECT_OBJECTIVECASE"] = "I considered {0}"
FRAGMENTS["PERSONAL_PRONOUN_INDIRECTOBJECT_OBJECTIVECASE"] = "I gave {0} consideration"
FRAGMENTS["PERSONAL_PRONOUN_PREDICATENOUN_NOMINATIVECASE"] = "The reason is {0}"
FRAGMENTS["PERSONAL_PRONOUN_OBJECTOFPREPOSITION_OBJECTIVECASE"] = "I thought about {0}"
FRAGMENTS["PERSONAL_PRONOUN_APPOSITIVE_NOMINATIVECASE"] = "The reason, {0}, worked"
FRAGMENTS["PERSONAL_PRONOUN_OBJECTIVECOMPLEMENT_OBJECTIVECASE"] = "I called the reason {0}"
FRAGMENTS["PERSONAL_PRONOUN_SUBJECT_OBJECTIVECASE"] = "I want {0} to work"
FRAGMENTS["PERSONAL_PRONOUN_PREDICATENOUN_OBJECTIVECASE"] = "I want it to be {0}"
FRAGMENTS["PERSONAL_PRONOUN_APPOSITIVE_OBJECTIVECASE"] = "I considered the reason, {0}"

SIMPLE_FRAGMENTS["PERSONAL_PRONOUN_SUBJECT_NOMINATIVECASE"] = "Happily {0} worked"
SIMPLE_FRAGMENTS["PERSONAL_PRONOUN_DIRECTOBJECT_OBJECTIVECASE"] = "consider {0}"
SIMPLE_FRAGMENTS["PERSONAL_PRONOUN_INDIRECTOBJECT_OBJECTIVECASE"] = "give {0} consideration"
SIMPLE_FRAGMENTS["PERSONAL_PRONOUN_PREDICATENOUN_NOMINATIVECASE"] = "be {0}"
SIMPLE_FRAGMENTS["PERSONAL_PRONOUN_OBJECTOFPREPOSITION_OBJECTIVECASE"] = "think about {0}"
SIMPLE_FRAGMENTS["PERSONAL_PRONOUN_APPOSITIVE_NOMINATIVECASE"] = "be the reason, {0},"
SIMPLE_FRAGMENTS["PERSONAL_PRONOUN_APPOSITIVE_OBJECTIVECASE"] = "consider the reason, {0},"

##### Verb Fragments

# main verb

FRAGMENTS["VERB_MAINVERB_SIMPLEPAST_LINKING_SINGULAR"] = "I {0} good"
FRAGMENTS["VERB_MAINVERB_SIMPLEPAST_LINKING_PLURAL"] = "They {0} good"
FRAGMENTS["VERB_MAINVERB_SIMPLEPAST_TRANSITIVE_SINGULAR"] = "I {0} it"
FRAGMENTS["VERB_MAINVERB_SIMPLEPAST_TRANSITIVE_PLURAL"] = "They {0} it"
FRAGMENTS["VERB_MAINVERB_SIMPLEPAST_INTRANSITIVE_SINGULAR"] = "I {0}"
FRAGMENTS["VERB_MAINVERB_SIMPLEPAST_INTRANSITIVE_PLURAL"] = "They {0}"

FRAGMENTS["VERB_MAINVERB_SIMPLEPRESENT_LINKING_SINGULAR"] = "I {0} good"
FRAGMENTS["VERB_MAINVERB_SIMPLEPRESENT_LINKING_SINGULAR_HE"] = "He {0} good"
FRAGMENTS["VERB_MAINVERB_SIMPLEPRESENT_LINKING_PLURAL"] = "They {0} good"
FRAGMENTS["VERB_MAINVERB_SIMPLEPRESENT_TRANSITIVE_SINGULAR"] = "I {0} it"
FRAGMENTS["VERB_MAINVERB_SIMPLEPRESENT_TRANSITIVE_SINGULAR_HE"] = "He {0} it"
FRAGMENTS["VERB_MAINVERB_SIMPLEPRESENT_TRANSITIVE_PLURAL"] = "They {0} it"
FRAGMENTS["VERB_MAINVERB_SIMPLEPRESENT_INTRANSITIVE_SINGULAR"] = "I {0}"
FRAGMENTS["VERB_MAINVERB_SIMPLEPRESENT_INTRANSITIVE_SINGULAR_HE"] = "He {0}"
FRAGMENTS["VERB_MAINVERB_SIMPLEPRESENT_INTRANSITIVE_PLURAL"] = "They {0}"

FRAGMENTS["VERB_MAINVERB_SIMPLEFUTURE_LINKING_SINGULAR"] = "I will {0} good"
FRAGMENTS["VERB_MAINVERB_SIMPLEFUTURE_LINKING_PLURAL"] = "They will {0} good"
FRAGMENTS["VERB_MAINVERB_SIMPLEFUTURE_TRANSITIVE_SINGULAR"] = "I will {0} it"
FRAGMENTS["VERB_MAINVERB_SIMPLEFUTURE_TRANSITIVE_PLURAL"] = "They will {0} it"
FRAGMENTS["VERB_MAINVERB_SIMPLEFUTURE_INTRANSITIVE_SINGULAR"] = "I will {0}"
FRAGMENTS["VERB_MAINVERB_SIMPLEFUTURE_INTRANSITIVE_PLURAL"] = "They will {0}"

FRAGMENTS["VERB_MAINVERB_PERFECTPAST_LINKING_SINGULAR"] = "I had {0} good"
FRAGMENTS["VERB_MAINVERB_PERFECTPAST_LINKING_PLURAL"] = "They had {0} good"
FRAGMENTS["VERB_MAINVERB_PERFECTPAST_TRANSITIVE_SINGULAR"] = "I had {0} it"
FRAGMENTS["VERB_MAINVERB_PERFECTPAST_TRANSITIVE_PLURAL"] = "They had {0} it"
FRAGMENTS["VERB_MAINVERB_PERFECTPAST_INTRANSITIVE_SINGULAR"] = "I had {0}"
FRAGMENTS["VERB_MAINVERB_PERFECTPAST_INTRANSITIVE_PLURAL"] = "They had {0}"

FRAGMENTS["VERB_MAINVERB_PERFECTPRESENT_LINKING_SINGULAR"] = "I have {0} good"
FRAGMENTS["VERB_MAINVERB_PERFECTPRESENT_LINKING_PLURAL"] = "They have {0} good"
FRAGMENTS["VERB_MAINVERB_PERFECTPRESENT_TRANSITIVE_SINGULAR"] = "I have {0} it"
FRAGMENTS["VERB_MAINVERB_PERFECTPRESENT_TRANSITIVE_PLURAL"] = "They have {0} it"
FRAGMENTS["VERB_MAINVERB_PERFECTPRESENT_INTRANSITIVE_SINGULAR"] = "I have {0}"
FRAGMENTS["VERB_MAINVERB_PERFECTPRESENT_INTRANSITIVE_PLURAL"] = "They have {0}"

FRAGMENTS["VERB_MAINVERB_PERFECTFUTURE_LINKING_SINGULAR"] = "I will have {0} good"
FRAGMENTS["VERB_MAINVERB_PERFECTFUTURE_LINKING_PLURAL"] = "They will have {0} good"
FRAGMENTS["VERB_MAINVERB_PERFECTFUTURE_TRANSITIVE_SINGULAR"] = "I will have {0} it"
FRAGMENTS["VERB_MAINVERB_PERFECTFUTURE_TRANSITIVE_PLURAL"] = "They will have {0} it"
FRAGMENTS["VERB_MAINVERB_PERFECTFUTURE_INTRANSITIVE_SINGULAR"] = "I will have {0}"
FRAGMENTS["VERB_MAINVERB_PERFECTFUTURE_INTRANSITIVE_PLURAL"] = "They will have {0}"

FRAGMENTS["VERB_MAINVERB_PROGRESSIVEPAST_LINKING_SINGULAR"] = "I was {0} good"
FRAGMENTS["VERB_MAINVERB_PROGRESSIVEPAST_LINKING_PLURAL"] = "They were {0} good"
FRAGMENTS["VERB_MAINVERB_PROGRESSIVEPAST_TRANSITIVE_SINGULAR"] = "I was {0} it"
FRAGMENTS["VERB_MAINVERB_PROGRESSIVEPAST_TRANSITIVE_PLURAL"] = "They were {0} it"
FRAGMENTS["VERB_MAINVERB_PROGRESSIVEPAST_INTRANSITIVE_SINGULAR"] = "I was {0}"
FRAGMENTS["VERB_MAINVERB_PROGRESSIVEPAST_INTRANSITIVE_PLURAL"] = "They were {0}"

FRAGMENTS["VERB_MAINVERB_PROGRESSIVEPRESENT_LINKING_SINGULAR"] = "I am {0} good"
FRAGMENTS["VERB_MAINVERB_PROGRESSIVEPRESENT_LINKING_PLURAL"] = "They are {0} good"
FRAGMENTS["VERB_MAINVERB_PROGRESSIVEPRESENT_TRANSITIVE_SINGULAR"] = "I am {0} it"
FRAGMENTS["VERB_MAINVERB_PROGRESSIVEPRESENT_TRANSITIVE_PLURAL"] = "They are {0} it"
FRAGMENTS["VERB_MAINVERB_PROGRESSIVEPRESENT_INTRANSITIVE_SINGULAR"] = "I am {0}"
FRAGMENTS["VERB_MAINVERB_PROGRESSIVEPRESENT_INTRANSITIVE_PLURAL"] = "They are {0}"

FRAGMENTS["VERB_MAINVERB_PROGRESSIVEFUTURE_LINKING_SINGULAR"] = "I will be {0} good"
FRAGMENTS["VERB_MAINVERB_PROGRESSIVEFUTURE_LINKING_PLURAL"] = "They will be {0} good"
FRAGMENTS["VERB_MAINVERB_PROGRESSIVEFUTURE_TRANSITIVE_SINGULAR"] = "I will be {0} it"
FRAGMENTS["VERB_MAINVERB_PROGRESSIVEFUTURE_TRANSITIVE_PLURAL"] = "They will be {0} it"
FRAGMENTS["VERB_MAINVERB_PROGRESSIVEFUTURE_INTRANSITIVE_SINGULAR"] = "I will be {0}"
FRAGMENTS["VERB_MAINVERB_PROGRESSIVEFUTURE_INTRANSITIVE_PLURAL"] = "They will be {0}"

FRAGMENTS["VERB_MAINVERB_PERFECTPROGRESSIVEPAST_LINKING_SINGULAR"] = "I had been {0} good"
FRAGMENTS["VERB_MAINVERB_PERFECTPROGRESSIVEPAST_LINKING_PLURAL"] = "They had been {0} good"
FRAGMENTS["VERB_MAINVERB_PERFECTPROGRESSIVEPAST_TRANSITIVE_SINGULAR"] = "I had been {0} it"
FRAGMENTS["VERB_MAINVERB_PERFECTPROGRESSIVEPAST_TRANSITIVE_PLURAL"] = "They had been {0} it"
FRAGMENTS["VERB_MAINVERB_PERFECTPROGRESSIVEPAST_INTRANSITIVE_SINGULAR"] = "I had been {0}"
FRAGMENTS["VERB_MAINVERB_PERFECTPROGRESSIVEPAST_INTRANSITIVE_PLURAL"] = "They had been {0}"

FRAGMENTS["VERB_MAINVERB_PERFECTPROGRESSIVEPRESENT_LINKING_SINGULAR"] = "I have been {0} good"
FRAGMENTS["VERB_MAINVERB_PERFECTPROGRESSIVEPRESENT_LINKING_PLURAL"] = "They have been {0} good"
FRAGMENTS["VERB_MAINVERB_PERFECTPROGRESSIVEPRESENT_TRANSITIVE_SINGULAR"] = "I have been {0} it"
FRAGMENTS["VERB_MAINVERB_PERFECTPROGRESSIVEPRESENT_TRANSITIVE_PLURAL"] = "They have been {0} it"
FRAGMENTS["VERB_MAINVERB_PERFECTPROGRESSIVEPRESENT_INTRANSITIVE_SINGULAR"] = "I have been {0}"
FRAGMENTS["VERB_MAINVERB_PERFECTPROGRESSIVEPRESENT_INTRANSITIVE_PLURAL"] = "They have been {0}"

FRAGMENTS["VERB_MAINVERB_PERFECTPROGRESSIVEFUTURE_LINKING_SINGULAR"] = "I will have been {0} good"
FRAGMENTS["VERB_MAINVERB_PERFECTPROGRESSIVEFUTURE_LINKING_PLURAL"] = "They will have been {0} good"
FRAGMENTS["VERB_MAINVERB_PERFECTPROGRESSIVEFUTURE_TRANSITIVE_SINGULAR"] = "I will have been {0} it"
FRAGMENTS["VERB_MAINVERB_PERFECTPROGRESSIVEFUTURE_TRANSITIVE_PLURAL"] = "They will have been {0} it"
FRAGMENTS["VERB_MAINVERB_PERFECTPROGRESSIVEFUTURE_INTRANSITIVE_SINGULAR"] = "I will have been {0}"
FRAGMENTS["VERB_MAINVERB_PERFECTPROGRESSIVEFUTURE_INTRANSITIVE_PLURAL"] = "They will have been {0}"

# verbal

FRAGMENTS["VERB_INFINITIVE_SIMPLE_LINKING"] = "I want to {0} good"
FRAGMENTS["VERB_INFINITIVE_PERFECT_LINKING"] = "I want to have {0} good"
FRAGMENTS["VERB_INFINITIVE_PROGRESSIVE_LINKING"] = "I want to be {0} good"
FRAGMENTS["VERB_INFINITIVE_PERFECTPROGRESSIVE_LINKING"] = "I want to have been {0} good"

FRAGMENTS["VERB_INFINITIVE_SIMPLE_TRANSITIVE"] = "I want to {0} it"
FRAGMENTS["VERB_INFINITIVE_PERFECT_TRANSITIVE"] = "I want to have {0} it"
FRAGMENTS["VERB_INFINITIVE_PROGRESSIVE_TRANSITIVE"] = "I want to be {0} it"
FRAGMENTS["VERB_INFINITIVE_PERFECTPROGRESSIVE_TRANSITIVE"] = "I want to have been {0} it"

FRAGMENTS["VERB_INFINITIVE_SIMPLE_INTRANSITIVE"] = "I want to {0}"
FRAGMENTS["VERB_INFINITIVE_PERFECT_INTRANSITIVE"] = "I want to have {0}"
FRAGMENTS["VERB_INFINITIVE_PROGRESSIVE_INTRANSITIVE"] = "I want to be {0}"
FRAGMENTS["VERB_INFINITIVE_PERFECTPROGRESSIVE_INTRANSITIVE"] = "I want to have been {0}"

FRAGMENTS["VERB_INFINITIVE_SUBJECT"] = "To {0} is fun"
FRAGMENTS["VERB_INFINITIVE_DIRECTOBJECT"] = "I like to {0}"
FRAGMENTS["VERB_INFINITIVE_PREDICATENOUN"] = "To win is to {0}"
FRAGMENTS["VERB_INFINITIVE_OBJECTOFPREPOSITION"] = "The man about to {0} won"
FRAGMENTS["VERB_INFINITIVE_NOUNMODIFIER"] = "The man to {0} won"
FRAGMENTS["VERB_INFINITIVE_VERBMODIFIER"] = "I played to {0}"
FRAGMENTS["VERB_INFINITIVE_ADJECTIVEMODIFIER"] = "I am happy to {0}"
FRAGMENTS["VERB_INFINITIVE_ADVERBMODIFIER"] = "I won enough to {0}"

FRAGMENTS["VERB_PARTICIPLE_LINKING"] = "They, {0}, are good"
FRAGMENTS["VERB_PARTICIPLE_TRANSITIVE"] = "They, {0}, are good"
FRAGMENTS["VERB_PARTICIPLE_INTRANSITIVE"] = "They, {0}, are good"

FRAGMENTS["VERB_GERUND_LINKING"] = "I like {0} good"
FRAGMENTS["VERB_GERUND_TRANSITIVE"] = "I like {0} it"
FRAGMENTS["VERB_GERUND_INTRANSITIVE"] = "I like {0}"
FRAGMENTS["VERB_GERUND_SUBJECT"] = "I want {0} to be fun"
FRAGMENTS["VERB_GERUND_DIRECTOBJECT"] = "I like {0}"
FRAGMENTS["VERB_GERUND_PREDICATENOUN"] = "The action is {0}"
FRAGMENTS["VERB_GERUND_INDIRECTOBJECT"] = "I gave {0} a try"
FRAGMENTS["VERB_GERUND_OBJECTOFPREPOSITION"] = "I wrote about {0}"
FRAGMENTS["VERB_GERUND_OBJECTIVECOMPLEMENT"] = "I called the action {0}"

SIMPLE_FRAGMENTS["VERB_INFINITIVE_SIMPLE_LINKING"] = "{0} good"
SIMPLE_FRAGMENTS["VERB_INFINITIVE_PERFECT_LINKING"] = "have {0} good"
SIMPLE_FRAGMENTS["VERB_INFINITIVE_PROGRESSIVE_LINKING"] = "be {0} good"
SIMPLE_FRAGMENTS["VERB_INFINITIVE_PERFECTPROGRESSIVE_LINKING"] = "have been {0} good"

SIMPLE_FRAGMENTS["VERB_INFINITIVE_SIMPLE_TRANSITIVE"] = "{0} it"
SIMPLE_FRAGMENTS["VERB_INFINITIVE_PERFECT_TRANSITIVE"] = "have {0} it"
SIMPLE_FRAGMENTS["VERB_INFINITIVE_PROGRESSIVE_TRANSITIVE"] = "be {0} it"
SIMPLE_FRAGMENTS["VERB_INFINITIVE_PERFECTPROGRESSIVE_TRANSITIVE"] = "have been {0} it"

SIMPLE_FRAGMENTS["VERB_INFINITIVE_SIMPLE_INTRANSITIVE"] = "{0}"
SIMPLE_FRAGMENTS["VERB_INFINITIVE_PERFECT_INTRANSITIVE"] = "have {0}"
SIMPLE_FRAGMENTS["VERB_INFINITIVE_PROGRESSIVE_INTRANSITIVE"] = "be {0}"
SIMPLE_FRAGMENTS["VERB_INFINITIVE_PERFECTPROGRESSIVE_INTRANSITIVE"] = "have been {0}"

SIMPLE_FRAGMENTS["VERB_INFINITIVE_DIRECTOBJECT"] = "like to {0}"
SIMPLE_FRAGMENTS["VERB_INFINITIVE_PREDICATENOUN"] = "consider the action being to {0}"
SIMPLE_FRAGMENTS["VERB_INFINITIVE_OBJECTOFPREPOSITION"] = "see about to {0}"
SIMPLE_FRAGMENTS["VERB_INFINITIVE_NOUNMODIFIER"] = "see the man to {0}"
SIMPLE_FRAGMENTS["VERB_INFINITIVE_VERBMODIFIER"] = "play to {0}"
SIMPLE_FRAGMENTS["VERB_INFINITIVE_ADJECTIVEMODIFIER"] = "be happy to {0}"
SIMPLE_FRAGMENTS["VERB_INFINITIVE_ADVERBMODIFIER"] = "win enough to {0}"

SIMPLE_FRAGMENTS["VERB_PARTICIPLE_LINKING"] = "call them, {0}, good"
SIMPLE_FRAGMENTS["VERB_PARTICIPLE_TRANSITIVE"] = "call them, {0}, good"
SIMPLE_FRAGMENTS["VERB_PARTICIPLE_INTRANSITIVE"] = "call them, {0}, good"

SIMPLE_FRAGMENTS["VERB_GERUND_LINKING"] = "like {0} good"
SIMPLE_FRAGMENTS["VERB_GERUND_TRANSITIVE"] = "like {0} it"
SIMPLE_FRAGMENTS["VERB_GERUND_INTRANSITIVE"] = "like {0}"
SIMPLE_FRAGMENTS["VERB_GERUND_DIRECTOBJECT"] = "like {0}"
SIMPLE_FRAGMENTS["VERB_GERUND_PREDICATENOUN"] = "consider the action being {0}"
SIMPLE_FRAGMENTS["VERB_GERUND_INDIRECTOBJECT"] = "give {0} a try"
SIMPLE_FRAGMENTS["VERB_GERUND_OBJECTOFPREPOSITION"] = "write about {0}"
SIMPLE_FRAGMENTS["VERB_GERUND_OBJECTIVECOMPLEMENT"] = "call the action {0}"

##### Adjective Fragments

FRAGMENTS["ADJECTIVE_NOUNMODIFIER"] = "People are {0}"
FRAGMENTS["ADJECTIVE_PRONOUNMODIFIER"] = "It is {0}"
FRAGMENTS["ADJECTIVE_PREDICATEADJECTIVE"] = "They are {0}"
FRAGMENTS["ADJECTIVE_ADJACENTADJECTIVE"] = "I saw {0} people"
FRAGMENTS["ADJECTIVE_OBJECTIVECOMPLEMENT"] = "I declared it {0}"

SIMPLE_FRAGMENTS["ADJECTIVE_NOUNMODIFIER"] = "see {0} people"
SIMPLE_FRAGMENTS["ADJECTIVE_PRONOUNMODIFIER"] = "declare it {0}"
SIMPLE_FRAGMENTS["ADJECTIVE_PREDICATEADJECTIVE"] = "be {0}"
SIMPLE_FRAGMENTS["ADJECTIVE_ADJACENTADJECTIVE"] = "see {0} people"
SIMPLE_FRAGMENTS["ADJECTIVE_OBJECTIVECOMPLEMENT"] = "declare it {0}"

##### Adverb Fragments

FRAGMENTS["ADVERB_VERBMODIFIER"] = "They went {0}"
FRAGMENTS["ADVERB_VERBMODIFIER_FUTURE"] = "They will go {0}"
FRAGMENTS["ADVERB_VERBMODIFIER_PRE"] = "They {0} went"
FRAGMENTS["ADVERB_ADJECTIVEMODIFIER"] = "They are {0} magnificent"
FRAGMENTS["ADVERB_ADJECTIVEMODIFIER_MUCH"] = "They are {0} better"
FRAGMENTS["ADVERB_ADJECTIVEMODIFIER_POST"] = "They are magnificent {0}"
FRAGMENTS["ADVERB_ADVERBMODIFIER"] = "They acted {0} magnificently"
FRAGMENTS["ADVERB_ADVERBMODIFIER_MUCH"] = "They acted {0} better"
FRAGMENTS["ADVERB_ADVERBMODIFIER_POST"] = "They acted magnificently {0}"

SIMPLE_FRAGMENTS["ADVERB_VERBMODIFIER"] = "go {0}"
SIMPLE_FRAGMENTS["ADVERB_VERBMODIFIER_FUTURE"] = "go {0}"
SIMPLE_FRAGMENTS["ADVERB_VERBMODIFIER_PRE"] = "consider {0} going"
SIMPLE_FRAGMENTS["ADVERB_ADJECTIVEMODIFIER"] = "be {0} magnificent"
SIMPLE_FRAGMENTS["ADVERB_ADJECTIVEMODIFIER_MUCH"] = "be {0} better"
SIMPLE_FRAGMENTS["ADVERB_ADJECTIVEMODIFIER_POST"] = "be magnificent {0}"
SIMPLE_FRAGMENTS["ADVERB_ADVERBMODIFIER"] = "act {0} magnificently"
SIMPLE_FRAGMENTS["ADVERB_ADVERBMODIFIER_MUCH"] = "act {0} better"
SIMPLE_FRAGMENTS["ADVERB_ADVERBMODIFIER_POST"] = "act magnificently {0}"

##### Preposition Fragments

FRAGMENTS["PREPOSITION_INTROTOADJECTIVE"] = "Those {0} it acted"
FRAGMENTS["PREPOSITION_INTROTOADVERB"] = "It acted {0} it"

SIMPLE_FRAGMENTS["PREPOSITION_INTROTOADJECTIVE"] = "consider those {0} it"
SIMPLE_FRAGMENTS["PREPOSITION_INTROTOADVERB"] = "act {0} it"

##### Conjunction Fragments

FRAGMENTS["CONJUNCTION_SUBORDINATOR"] = "I ran {0} I ran"
FRAGMENTS["CONJUNCTION_CONJUNCTIVE"] = "I ran; {0}, I ran"

##### Interjection Fragments

FRAGMENTS["INTERJECTION_"] = "{0}, I win"

################################################## sentence construction

def default_p3(_p2_):
    if _p2_ == "NOUN":
        return "SUBJECT"
    if _p2_ == "PRONOUN":
        return "SUBJECT"
    if _p2_ == "VERB":
        return "MAINVERB"
    if _p2_ == "ADJECTIVE":
        return "NOUNMODIFIER"
    if _p2_ == "ADVERB":
        return "VERBMODIFIER"
    if _p2_ == "PREPOSITION":
        return "INTROTOADJECTIVE"
    if _p2_ == "CONJUNCTION":
        return "CONJUNCTIVE"
    return ""

def get_basic_sentence_fragment(P1, P2, P3):
    # input: player one demand P1, player two demand P2, player three demand P3
    c = CLAUSES
    p = PHRASES
    if (c,p) not in BASIC_SENTENCE_FRAGMENTS.keys():
        c = c[::-1]
        p = p[::-1]
    if P1 == "SIMPLE" or P1 == "COMPOUND":
        return "{0}" if p == () else SIMPLE_SENTENCE_FRAGMENTS[((),p)]
    if P2 == "NOUN" or P2 == "PRONOUN":
        if "OBJECTIVECASE" in GENERALS:
            if P3 in ["SUBJECT","PREDICATENOUN"]:
                c = tuple(x for x in c if x not in ["INFINITIVE","NOUN"])
    return BASIC_SENTENCE_FRAGMENTS[(c,p)]

def get_sentence(P1):
    # input: player one demand P1
    return SENTENCES[P1]

def get_fragment(P1, P2, P3, w):
    # input: player one demand P1, player two demand P2, player three demand P3, Word w
    key = P2 + "_" + P3
    if P2 == "VERB":
        if P3 == "AUXILIARY":
            if (P1 == "SIMPLE" or P1 == "COMPOUND") and PHRASES != ():
                return w.usei
            return w.use
        else:
            key = P2 + verb_get_suffix(w)
    if P2 == "NOUN" or P2 == "PRONOUN":
        addedcase = False
        if "OBJECTIVECASE" in GENERALS:
            if P3 in ["SUBJECT","PREDICATENOUN","APPOSITIVE"]:
                key = key + "_OBJECTIVECASE"
                addedcase = True
        if P2 == "PRONOUN":
            case = "_NOMINATIVECASE" if "NOMINATIVECASE" in w.specials else "_OBJECTIVECASE"
            if "NOMINATIVECASE" in w.specials and "OBJECTIVECASE" in w.specials:
                if P3 not in ["SUBJECT","PREDICATENOUN","APPOSITIVE"]:
                    case = "_OBJECTIVECASE"
                if "OBJECTIVECASE" in GENERALS:
                    case = "_OBJECTIVECASE"
            if "DEMONSTRATIVE" in w.specials or "INDEFINITE" in w.specials:
                pass
            elif "PERSONAL" in w.specials:
                if "POSSESSIVECASE" not in w.specials:
                    key = "PERSONAL_" + key
                    if not addedcase:
                        key = key + case
                        addedcase = True
            elif "RELATIVE" in w.specials:
                free_addon = ("FREE_" if "FREE" in w.specials else "")
                key = free_addon + "RELATIVE_" + key
                if not addedcase:
                    key = key + case
                    addedcase = True
            elif "INTERROGATIVE" in w.specials:
                if not addedcase:
                    key = key + case
                    addedcase = True
                key = "INTERROGATIVE_" + key
    if P2 == "ADVERB":
        if P3 == "VERBMODIFIER":
            if "PRE" in w.specials:
                key = key + "_PRE"
            elif "FUTURE" in w.specials:
                key = key + "_FUTURE"
        elif P3 == "ADJECTIVEMODIFIER":
            if "MUCH" in w.specials:
                key = key + "_MUCH"
            elif "POST" in w.specials:
                key = key + "_POST"
        elif P3 == "ADVERBMODIFIER":
            if "MUCH" in w.specials:
                key = key + "_MUCH"
            elif "POST" in w.specials:
                key = key + "_POST"
    if P1 == "SIMPLE" or P1 == "COMPOUND":
        if CLAUSES != ():
            return SIMPLE_FRAGMENTS["badkey"]
        if PHRASES != ():
            if P3 == "SUBJECT":
                return SIMPLE_FRAGMENTS["badkey"]
            return SIMPLE_FRAGMENTS[key].format(w.word)
    return FRAGMENTS[key].format(w.word)

def construct_correct_sentence():
    P1 = PLAYERONE if PLAYERONE else "SV"
    P2 = PLAYERTWO if PLAYERTWO else "NOUN"
    P3 = PLAYERTHREE if PLAYERTHREE else default_p3(P2)
    initialize_dictionary(P2)
    www = None
    for w in DICTIONARY:
        if word_is_valid(w,P1,P2,P3):
            www = w
            break
        else:
            pass
    A = get_sentence(P1)
    B = get_fragment(P1,P2,P3,www)
    C = get_basic_sentence_fragment(P1,P2,P3)
    X = A.format(C.format(B))
    X = X.replace(",.",".")
    X = X.replace("?,","?")
    X = X.replace("?.","?")
    Xfind = X.find("? and")
    if Xfind != -1:
        X = X[:Xfind] + " and how did you win?"
    return X

def win():
    return construct_correct_sentence()

################################################## website stuff
app = Flask(__name__)
app.config['SECRET_KEY'] = 'random string'
app.debug = True

# enable checkboxes
class CheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label = False)
    option_widget = widgets.CheckboxInput()

class StartForm(FlaskForm):
    player1 = SelectField("Player 1", choices = [("SV", "S-V"), ("SVDO", "S-V-DO"), ("SVIODO", "S-V-IO-DO"), ("SLVPN", "S-LV-PN"), ("SLVPA", "S-LV-PA"), ("SVDOOC(N)", "S-V-DO-OC(noun)"), ("SVDOOC(A)", "SV-DO-OC(adjective)"), ("SIMPLE", "simple"), ("COMPOUND", "compound"), ("COMPLEX", "complex"), ("COMPOUNDCOMPLEX", "compound-complex"), ("DECLARATIVE", "declarative"), ("INTERROGATIVE", "interrogative"), ("IMPERATIVE", "imperative"), ("EXCLAMATORY", "exclamatory"), ("INVERTED", "inverted")])
    player2and3 = SelectField("Player 2 and player 3", choices = [("NOUN_SUBJECT", "NOUN Subject"), ("NOUN_DIRECTOBJECT", "NOUN Direct Object"), ("NOUN_INDIRECTOBJECT", "NOUN Indirect Object"), ("NOUN_PREDICATENOUN", "NOUN Predicate Noun"), ("NOUN_OBJECTIVECOMPLEMENT", "NOUN Objective Complement"), ("NOUN_OBJECTOFPREPOSITION", "NOUN Object of the Preposition"), ("NOUN_APPOSITIVE", "NOUN Appositive"), ("NOUN_NOUNUSEDASADJECTIVE", "NOUN Noun Used as Adjective"), ("PRONOUN_SUBJECT", "PRONOUN Subject"), ("PRONOUN_DIRECTOBJECT", "PRONOUN Direct Object"), ("PRONOUN_INDIRECTOBJECT", "PRONOUN Indirect Object"), ("PRONOUN_PREDICATENOUN", "PRONOUN Predicate Noun"), ("PRONOUN_OBJECTIVECOMPLEMENT", "PRONOUN Objective Complement"), ("PRONOUN_OBJECTOFPREPOSITION", "PRONOUN Object of the Preposition"), ("PRONOUN_APPOSITIVE", "PRONOUN Appositive"), ("VERB_MAINVERB", "VERB Main Verb"), ("VERB_VERBAL", "VERB Verbal"), ("VERB_INFINITIVE", "VERB Infinitive"), ("VERB_GERUND", "VERB Gerund"), ("VERB_PARTICIPLE", "VERB Participle"), ("VERB_AUXILIARY", "VERB Auxiliary"), ("ADJECTIVE_NOUNMODIFIER", "ADJECTIVE Noun Modifier"), ("ADJECTIVE_PRONOUNMODIFIER", "ADJECTIVE Pronoun Modifier"), ("ADJECTIVE_PREDICATEADJECTIVE", "ADJECTIVE Predicate Adjective"), ("ADJECTIVE_OBJECTIVECOMPLEMENT", "ADJECTIVE Objective Complement"), ("ADJECTIVE_ADJACENTADJECTIVE", "ADJECTIVE Adjacent Adjective"), ("ADVERB_VERBMODIFIER", "ADVERB Verb Modifier"), ("ADVERB_ADJECTIVEMODIFIER", "ADVERB Adjective Modifier"), ("ADVERB_ADVERBMODIFIER", "ADVERB Adverb Modifier"), ("PREPOSITION_INTROTOADJECTIVE", "PREPOSITION Introductory word in an Adjective Phrase"), ("PREPOSITION_INTROTOADVERB", "PREPOSITION Introductory word in an Adverb Phrase"), ("CONJUNCTION_SUBORDINATOR", "CONJUNCTION Subordinator"), ("CONJUNCTION_CONJUNCTIVE", "CONJUNCTION Conjunctive Adverb"), ("INTERJECTION_", "INTERJECTION ")])
    colorWild = SelectField("Color Wild", choices = [("", "None"), ("BLACK", "Black"), ("GREEN", "Green"), ("ORANGE", "Orange"), ("PINK", "Pink"), ("RED", "Red"), ("YELLOW", "Yellow")])
    numLetters = IntegerField("Number of letters:")
    doubleVowel = RadioField("Double vowel?", choices = [("True", "Yes"), ("False", "No")])
    doubleConsonant = RadioField("Double consonant?", choices = [("True", "Yes"), ("False", "No")])
    mustContain = StringField("Must contain:")
    mustNotContain = StringField("Must not contain:")
    letterTransfer = StringField("Letter transfer (enter 2 letters; first letter to second letter)")
    functions = StringField("Functions (i.e. collective, present perfect, etc):")
    clauses = StringField("Clauses (separate with comma):")
    phrases = StringField("Phrases (separate with comma):")
    useCubes = RadioField("Use cubes?", choices = [("True", "Yes"), ("False", "No")])
    blackCubes = StringField("BLACK")
    greenCubes = StringField("GREEN")
    orangeCubes = StringField("ORANGE")
    pinkCubes = StringField("PINK")
    redCubes = StringField("RED")
    yellowCubes = StringField("YELLOW")
    submit = SubmitField('Submit')



@app.route('/', methods = ['GET', 'POST'])
def home():
    global PLAYERONE, PLAYERTWO, PLAYERTHREE, COLOR_WILD, NUMBER_OF_LETTERS, DOUBLE_VOWEL, DOUBLE_CONSONANT, MUST_CONTAIN, MUST_NOT_CONTAIN, LETTER_TRANSFER, GENERALS, CLAUSES, PHRASES, USE_CUBES, CUBES
    form = StartForm()
    if request.method == 'POST':
        # first 3 moves
        PLAYERONE = form.player1.data if form.player1.data != "None" else ""
        PLAYERTWO, PLAYERTHREE = form.player2and3.data.split('_') if form.player2and3.data != "None" else ["", ""]
        COLOR_WILD = form.colorWild.data
        
        # general demands
        NUMBER_OF_LETTERS = int(form.numLetters.data) if form.numLetters.data else 0
        DOUBLE_VOWEL = form.doubleVowel.data == "True"
        DOUBLE_CONSONANT = form.doubleConsonant.data == "True"
        MUST_CONTAIN = form.mustContain.data if form.mustContain.data else ""
        MUST_NOT_CONTAIN = form.mustNotContain.data if form.mustNotContain.data else ""
        LETTER_TRANSFER = list(form.letterTransfer.data) if form.letterTransfer.data else ["", ""]
        GENERALS = list(re.split(r", *", form.functions.data.upper())) if form.functions.data else []
        CLAUSES = tuple(re.split(r", *", form.clauses.data.upper())) if len(form.clauses.data) > 1 else tuple()
        PHRASES = tuple(re.split(r", *", form.phrases.data.upper())) if len(form.phrases.data) > 1 else tuple()

        # cubes
        CUBES = dict()
        USE_CUBES = False
        CUBES["BLACK"] = form.blackCubes.data if form.blackCubes.data else ""
        CUBES["GREEN"] = form.greenCubes.data if form.greenCubes.data else ""
        CUBES["ORANGE"] = form.orangeCubes.data if form.orangeCubes.data else ""
        CUBES["PINK"] = form.pinkCubes.data if form.pinkCubes.data else ""
        CUBES["RED"] = form.redCubes.data if form.redCubes.data else ""
        CUBES["YELLOW"] = form.yellowCubes.data if form.yellowCubes.data else ""
        for cube in CUBES:
            if CUBES[cube]:
                USE_CUBES = True

        # search for solution
        solution = win()

        # display solution
        return render_template('result.html', sentence = solution, sentenceLength = len(solution.split()), player1 = PLAYERONE, player2 = PLAYERTWO, player3 = PLAYERTHREE, colorWild = COLOR_WILD, numLetters = NUMBER_OF_LETTERS, doubleVowel = DOUBLE_VOWEL, doubleConsonant = DOUBLE_CONSONANT, mustCotain = MUST_CONTAIN, mustNotContain = MUST_NOT_CONTAIN, letterTransfer = LETTER_TRANSFER, functions = GENERALS, clauses = CLAUSES, phrases = PHRASES)
    return render_template('index.html', form = form)


################################################## main

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = int(os.getenv('PORT', 5000)))


