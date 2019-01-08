from MrLing import win
from MrBasicWff import BASIC_get_proof_string
from MrRegularWff import REGULAR_get_proof_string

import numpy as np
import pandas as pd
import os
from os import listdir
from os.path import isfile, join

from flask import Flask, request, render_template, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField, SelectMultipleField, RadioField, widgets
from wtforms.validators import Required
import re

################################################## website stuff

app = Flask(__name__)
app.config['SECRET_KEY'] = 'random string'
app.debug = True

# enable checkboxes
class CheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label = False)
    option_widget = widgets.CheckboxInput()

"""

class StartForm(FlaskForm):
    game = RadioField("Select Game", choices = [("WFF","WFF 'N Proof"),("Ling","Linguishtik")])
    submit = SubmitField('Submit')

class LingForm(FlaskForm):
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

class WffForm(FlaskForm):
    gametype = RadioField("Basic or Regular:", choices = [("Basic","Basic"),("Regular","Regular")])
    premises = StringField("Premises (separate with comma):")
    conclusion = StringField("Conclusion:")
    submit = SubmitField('Submit')

@app.route('/', methods = ['GET', 'POST'])
def home():
    form = StartForm()
    if request.method == 'POST':
        if form.game.data == "Ling":
            redirect(url_for('ling'))
        elif form.game.data == "WFF":
            redirect(url_for('wff'))
    return render_template('index.html', form = form)

@app.route('/ling', methods = ['GET', 'POST'])
def ling():
    global PLAYERONE, PLAYERTWO, PLAYERTHREE, COLOR_WILD, NUMBER_OF_LETTERS, DOUBLE_VOWEL, DOUBLE_CONSONANT, MUST_CONTAIN, MUST_NOT_CONTAIN, LETTER_TRANSFER, GENERALS, CLAUSES, PHRASES, USE_CUBES, CUBES
    form = LingForm()
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
        return render_template('ling_result.html', sentence = solution, sentenceLength = len(solution.split()), player1 = PLAYERONE, player2 = PLAYERTWO, player3 = PLAYERTHREE, colorWild = COLOR_WILD, numLetters = NUMBER_OF_LETTERS, doubleVowel = DOUBLE_VOWEL, doubleConsonant = DOUBLE_CONSONANT, mustCotain = MUST_CONTAIN, mustNotContain = MUST_NOT_CONTAIN, letterTransfer = LETTER_TRANSFER, functions = GENERALS, clauses = CLAUSES, phrases = PHRASES)
    return render_template('ling_index.html', form = form)

@app.route('/wff', methods = ['GET', 'POST'])
def wff():
    form = WffForm()
    if request.method == 'POST':
        get_proof_string = (BASIC_get_proof_string if form.gametype.data == "Basic" else REGULAR_get_proof_string)
        prems = [str(w) for w in form.premises.data]
        concl = str(form.conclusion.data)
        solution = get_proof_string(prems,concl)
        return render_template('wff_result.html', sentence = solution, gametype = form.gametype.data, premises = prems, conclusion = concl)
    return render_template('wff_index.html', form = form)
    
"""

class WffForm(FlaskForm):
    gametype = RadioField("Basic or Regular:", choices = [("Basic","Basic"),("Regular","Regular")])
    premises = StringField("Premises (separate with comma):")
    conclusion = StringField("Conclusion:")
    submit = SubmitField('Submit')

@app.route('/', methods = ['GET', 'POST'])
def wff():
    form = WffForm()
    if request.method == 'POST':
        get_proof_string = (BASIC_get_proof_string if form.gametype.data == "Basic" else REGULAR_get_proof_string)
        prems = [str(w) for w in form.premises.data]
        concl = str(form.conclusion.data)
        solution = get_proof_string(prems,concl)
        return render_template('wff_result.html', sentence = solution, gametype = form.gametype.data, premises = prems, conclusion = concl)
    return render_template('wff_index.html', form = form)

################################################## main

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = int(os.getenv('PORT', 5000)))

