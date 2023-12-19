###yunyang###
###Final Project###

import csv
import pandas as pd
import os
import string
import re
from bs4 import BeautifulSoup
import random

#import filtered csv
Question_top100_df = pd.read_csv('filtered_questions_top100_df.csv', encoding='ISO-8859-1')
filtered_answers_df= pd.read_csv('filtered_answers_df.csv', encoding='ISO-8859-1')
filtered_tags_df= pd.read_csv('filtered_tags_df.csv', encoding='ISO-8859-1')
tags_grouped = filtered_tags_df.groupby('Id')['Tag'].apply(set).reset_index()
matched_question= []
#import txt file
# Print the current working directory
current_directory = os.getcwd()
#print("Current Working Directory:", current_directory)
file_name = "interview_questions.txt"
file_path = os.path.join(current_directory, file_name)
# Check if the file exists
if os.path.isfile(file_path):
    #print("File found. Reading the file...")
    questions_list = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:  # Specify UTF-8 encoding
            questions_list = [line.strip() for line in file]
        #print("Questions read from the file:")
        #for index, question in enumerate(questions_list):
            #print(f"{index}: {question}")
    except UnicodeDecodeError as e:
        print(f"UnicodeDecodeError: {e}. You might need to check the file encoding.")
else:
    print(f"File not found at {file_path}. Please check the file location and name.")

def main():
    print("This is a program that helps you thinking about learning python via interview questions.")
    print("I have some interview questions to help you get prepared.")
    loadLoop= True
    while loadLoop:
        whetherLoadTree= input("Would you like to load a question tree from a file? ")
        if whetherLoadTree== "yes":
            loop= True
            filename= input("What's the name of the file? ")
            tree= loadTree(filename)
            global matched_question
            with open("questionList.txt", "r") as file:
                matched_question = [line.strip() for line in file]
            if tree== "Error":
                print("File not Found. Please try again.")
            else:
                tree= play(tree)
                printTree(tree)
        else:
            loadLoop= False
            # User first input
            while True:
                user_input = input("Please type a number from 0 to 20 to get started: ")
                if is_int_between_0_and_20(user_input):
                    print("Valid input. Continuing...")
                    break
                else:
                    print("Invalid input. Please try again.")
            user_input = int(user_input)
            simple_question = questions_list[user_input]
            print(simple_question)
            print("\nDue to limited dataset, I do not have the answer to this question.")
            print("But I happen to know the answers to the similar questions.")
            simple_question_keywords = extract_keywords(simple_question)
            print("Here are some keywords: ", simple_question_keywords)
            complex_questions_list = Question_top100_df['Title'].tolist()
            matched_complex_questions = match_complex_questions(simple_question_keywords, complex_questions_list)
            matched_question = matched_complex_questions
            with open("questionList.txt", "w") as file:
                for item in matched_complex_questions:
                    file.write(item + "\n")
            for index, question in enumerate(matched_complex_questions):
                print(f"{index}: {question}")

            # User second input
            while True:
                user_second_input = input("Please type the index number of the following questions to explore: ")
                if is_int_between_0_and_9(user_second_input):
                    print("Valid input. Continuing...")
                    break
                else:
                    print("Invalid input. Please try again.")
            user_second_input = int(user_second_input)
            found_id = find_id_by_title(Question_top100_df, matched_complex_questions[user_second_input])
            print("Question Id: ", found_id, "\n")
            top_answer= find_the_top_answer(found_id, filtered_answers_df)
            #print(top_answer)

            # find a similar question
            random_number= random_number_except(user_second_input)
            similar_question_Id = find_id_by_title(Question_top100_df, matched_complex_questions[random_number])
            similar_question=Question_top100_df.loc[Question_top100_df['Id'] == similar_question_Id, 'Title'].iloc[0]
            similar_top_answer= find_the_top_answer(similar_question_Id, filtered_answers_df)

            # build trees
            mediumTree = \
                (complex_questions_list[user_second_input],
                    (similar_question,
                        (str(similar_question_Id), None, None),
                        (str(similar_question_Id), None, None)),
                    (str(found_id), None, None))
            #printTree(mediumTree)
            tree= mediumTree
            print("Now let's test if you have knowledge to pass the interview. Type yes if you know the answer, type no if you don't.")
            tree= play(tree)
            printTree(tree)

        while True:
            search_answer= int(input("please input the id of the question for its answer: "))
            answer= find_the_top_answer(search_answer, filtered_answers_df)
            print("The answer is: ")
            if answer == "I do not have an answer to this question.":
                print(answer)
            else: 
                answer= to_text(answer)
                print(answer)
            yes_or_no= input("Do you want to check another one? (yes or no) ")
            if yes_or_no != "yes":
                break

        whetherSaveTree= input("Would you like to save this tree for later? ")
        if whetherSaveTree== "yes":
            loadLoop= False
            newFilename= input("Please enter a file name:")
            treeFile = open(newFilename, 'w')
            saveTree(tree, treeFile)
            treeFile.close()
            #printSaveTree(filename)
            print("Thank you! The file has been saved.")
            print("Bye!")
        elif whetherSaveTree== "no":
            print("Bye!")
            loop=False
            loadLoop= False
        else:
            print("yes or no?")

def is_int_between_0_and_20(value):
    try:
        int_value = int(value)
        return 0 <= int_value <= 20
    except ValueError:
        return False

def is_int_between_0_and_9(value):
    try:
        int_value = int(value)
        return 0 <= int_value <= 9
    except ValueError:
        return False

def simple_stem(word):
    # Basic stemming: remove 's' at the end of the word
    # Note: This is a very simplistic approach and may not be accurate for all words
    if word.endswith('s'):
        return word[:-1]
    return word

def extract_keywords(sentence):
    # Define a set of stopwords
    stopwords = set(['the', 'what', 'is', 'how', 'do', 'does', 'explain', 'in', 'a', 'an', 'one','would','many','you','are','them','and','are'])
    sentence = sentence.translate(str.maketrans('', '', string.punctuation))
    keywords = set(simple_stem(word.lower()) for word in sentence.split() if word.lower() not in stopwords)
    return keywords

def match_complex_questions(simple_question_keywords, complex_questions):
    # Score each complex question based on keyword matches
    match_scores = {}
    for complex_question in complex_questions:
        complex_question_keywords = extract_keywords(complex_question)
        common_keywords = simple_question_keywords.intersection(complex_question_keywords)

        # Check if there is at least one common keyword
        if len(common_keywords) > 0:
            match_scores[complex_question] = len(common_keywords)

    # Sort complex questions based on their match score
    sorted_complex_questions = sorted(match_scores, key=match_scores.get, reverse=True)

    # Return the top 10 matches
    return sorted_complex_questions[:10]

def find_id_by_title(df, title):
    matching_rows = df[df['Title'] == title]
    if not matching_rows.empty:
        return matching_rows['Id'].iloc[0]
    else:
        return None  # or any appropriate value indicating not found

def find_the_top_answer(question_id, answers_df):
    # Filter answers for the specific question
    filtered_answers = answers_df[answers_df['ParentId'] == question_id]

    # Sort the answers by Score in descending order and select the top two
    top_answer = filtered_answers.sort_values(by='Score', ascending=False).head(1)
    answer= top_answer["Body"].tolist()
    if answer == []:
        answer= ["I do not have an answer to this question."]
        #print("The answer to the question you can not solve is: ")
        #print(answer[0])
        return (answer[0])
    else:
        #print("The answer to the question you can not solve is: ")
        #to_text(answer[0])
        return ((answer[0]))

def to_text(answer):
    soup = BeautifulSoup(answer,features="html.parser")
    print(soup.get_text())

def random_number_except(exclude):
    """
    Generate a random number between 0 and 9 (inclusive), excluding the 'exclude' number.

    Args:
    exclude (int): The number to exclude from the random selection.

    Returns:
    int: A random number between 0 and 9 (inclusive) except 'exclude'.
    """
    # Create a list of numbers from 0 to 9, excluding 'exclude'.
    numbers = [i for i in range(10) if i != exclude]

    # Generate a random index within the valid range of numbers.
    random_index = random.randint(0, len(numbers) - 1)

    # Return the randomly selected number.
    return numbers[random_index]

def printTree(tree, prefix = '', bend = '', answer = ''):
    """Recursively print a 20 Questions tree in a human-friendly form.
       TREE is the tree (or subtree) to be printed.
       PREFIX holds characters to be prepended to each printed line.
       BEND is a character string used to print the "corner" of a tree branch.
       ANSWER is a string giving "Yes" or "No" for the current branch."""
    text, left, right = tree
    if left is None  and  right is None:
        print(f'{prefix}{bend}{answer}It is {text}')
    else:
        print(f'{prefix}{bend}{answer}{text}')
        if bend == '+-':
            prefix = prefix + '| '
        elif bend == '`-':
            prefix = prefix + '  '
        printTree(left, prefix, '+-', "Yes: ")
        printTree(right, prefix, '`-', "No:  ")

def addLeaf(tree,path):
    """
    Updates the decision tree by adding a new leaf based on user input.

    This function traverses the tree according to user responses. 
    If it reaches a leaf, it asks the user to confirm the guess. 
    If the guess is incorrect, it adds a new leaf with the correct answer 
    and an associated question to distinguish it from the existing leaf.

    Parameters:
    tree (tuple): The current node of the decision tree.
    path (list): The path taken in the tree to reach the current node.

    Returns:
    tuple: The updated tree with the new leaf added.
    """
    if tree[1] is None and tree[2] is None: # isAnswer
        user_answer= input("Please check this Id for the answer to the previous question: "+tree[0]+"\nType yes if you want to end the game, no, if you want to add one more question for the next time: ")
        if user_answer== "yes":
            print('well done!')
            return True
        elif user_answer== "no":
            newTree= tree
            while True:
                    correctAnswer= input('please type a different number from 0-9: ')
                    if is_int_between_0_and_9(correctAnswer):
                        break
                    else:
                        print("Invalid input. Please try again.")
            correctAnswer=int(correctAnswer)
            global matched_question
            similar_question_Id = find_id_by_title(Question_top100_df, matched_question[correctAnswer])
            distinguish= Question_top100_df.loc[Question_top100_df['Id'] == similar_question_Id, 'Title'].iloc[0]
            newTree= (distinguish, tree, (similar_question_Id,None,None))
            print("You add the question Id:", similar_question_Id, distinguish)
            #print(tree)
            #print(newTree)
            #print(path)
            return newTree
        else:
            print('error')
            exit(0)
    else: #isQuestion
        user_answer= input(tree[0]+" ")
        if user_answer== "yes":
            path.append(1)
            #print(path)
            return addLeaf(tree[1],path)
        elif user_answer== "no":
            path.append(2)
            #print(path)
            return addLeaf(tree[2],path)
        else:
            print('error')
            exit(0)

def replace_nested_element_in_tuple(tree, indices, new_value):
    """
    Replaces an element in a nested tuple structure.

    Parameters:
    tree (tuple): The original tuple structure.
    indices (list of int): A list of indices specifying the path to the element to be replaced.
    new_value: The new value to replace the element at the specified location.

    Returns:
    tuple: The modified tuple with the specified element replaced.
    """
    if not indices:
        return new_value
    index = indices[0]
    if len(indices) == 1:
        return tree[:index] + (new_value,) + tree[index + 1:]
    else:
        return tree[:index] + (replace_nested_element_in_tuple(tree[index], indices[1:], new_value),) + tree[index + 1:]

def play(tree):
    """
    Conducts a round of the game, updating the tree with a new leaf if necessary.

    Parameters:
    tree (tuple): The decision tree to play with.

    Returns:
    tuple: The updated decision tree after playing.
    """
    path=[]
    newLeaf= addLeaf(tree,path)
    if newLeaf!= True:
        newTree= replace_nested_element_in_tuple(tree, path, newLeaf)
        #print(newTree)
        return newTree
    else:
        return tree

def saveTree(tree,filename):
    """
    Recursively saves a decision tree to a file in a predefined format.

    Parameters:
    tree (tuple): The decision tree to be saved.
    filename (file object): The file to which the tree will be saved.
    """
    text, left, right = tree
    if left is None and right is None:#isLeaf
        print("Leaf",file= filename)
        print(text,file= filename)
    else:#isInternalNode
        print("Internal Node",file= filename)
        print(text,file= filename)
        saveTree(left,filename)
        saveTree(right,filename)

def parse_tree(lines):
    """
    Parses a list of strings into a decision tree structure.

    Parameters:
    lines (list of str): The lines of text representing the tree.

    Returns:
    tuple: The decision tree as a nested tuple structure, or None if the list is empty.
    """
    if not lines:
        return None

    line = lines.pop(0).strip()
    if line.startswith('Internal Node'):
        text = lines.pop(0).strip()
        left = parse_tree(lines)
        right = parse_tree(lines)
        return (text, left, right)
    elif line.startswith('Leaf'):
        answer = lines.pop(0).strip()
        return (answer, None, None)
    else:
        raise ValueError(f"Invalid line: {line}")

def loadTree(filename):
    """
    Loads a decision tree from a specified file.

    Parameters:
    filename (str): The path to the file containing the tree data.

    Returns:
    tuple: The decision tree loaded from the file, represented as a nested tuple structure.
    """
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
        return parse_tree(lines)
    except FileNotFoundError:
        return "Error"
if __name__ == '__main__':
    main()