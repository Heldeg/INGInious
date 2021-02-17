# -*- coding: utf-8 -*-
#
# This file is part of UNCode. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Rubric scoring page """
import os

import web
import re
import types
from bson.objectid import ObjectId
from ast import literal_eval

from inginious.frontend.pages.api._api_page import APIError
from inginious.frontend.parsable_text import ParsableText
from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from inginious.frontend.plugins.manual_scoring.pages.constants import get_use_minify, get_render_path
from inginious.frontend.plugins.manual_scoring.pages.manual_scoring_error import ManualScoringError
from inginious.frontend.plugins.utils import read_json_file, get_mandatory_parameter

base_renderer_path = get_render_path()


def get_manual_scoring_data(submission):
    """ return the comment, score and rubric status if they are storage """
    comment = ""
    score = "No grade"
    rubric = []

    if 'manual_scoring' in submission:
        score = submission['manual_scoring']['grade']
        comment = submission['manual_scoring']['comment']
        rubric = submission['manual_scoring']['rubric_status']

    return comment, score, rubric


def get_submission_result_text(submission_input):
    """ return the result of a submission """
    info = submission_input['text']
    pars_text = ParsableText(info)
    final_text = pars_text.parse()
    final_text = final_text.replace('\n', '')
    return final_text


def check_manual_scoring_data():
    manual_grade = get_mandatory_parameter(web.input(), "manual_grade")
    comment = get_mandatory_parameter(web.input(), "comment")
    rubric_status = get_mandatory_parameter(web.input(), "rubric")

    check_rubric_format(rubric_status)
    check_manual_grade_format(manual_grade)
    check_comment_format(comment)

    return manual_grade, comment, rubric_status


def check_rubric_format(rubric):
    rubric_id_list = check_string_is_list(rubric)

    rubric_len = len(rubric_id_list)
    rubric_max_len = 5
    id_regular_expression = re.compile(r"^([0-4]-[0-4])$")

    if rubric_len > rubric_max_len:
        raise ManualScoringError("List is too long")

    for element in rubric_id_list:
        if not id_regular_expression.match(element):
            raise ManualScoringError("One element doesn't have the correct format")


def check_string_is_list(rubric):
    error_text = "rubric need be a list"
    try:
        rubric = literal_eval(rubric)
        if isinstance(rubric, list):
            return rubric
        else:
            raise ManualScoringError(error_text)
    except ValueError:
        raise ManualScoringError(error_text)


def check_manual_grade_format(manual_grade):
    max_grade = 5
    min_grade = 0
    float_regular_expression = re.compile(r"^([0-9].[0-9])$")

    if not float_regular_expression.match(manual_grade):
        raise ManualScoringError("The grade doesn't have the correct format")

    manual_grade_number = float(manual_grade)

    if manual_grade_number > max_grade or manual_grade_number < min_grade:
        raise ManualScoringError("The grade is out of range")


def check_comment_format(comment):
    if not isinstance(comment, str):
        raise ManualScoringError("The comment isn't a string")


class ManualScoringPage(INGIniousAdminPage):
    """ Rubric scoring page to manual scoring """

    def GET_AUTH(self, course_id, task_id, submission_id):
        """ Get request """
        course, task = self.get_course_and_check_rights(course_id, task_id)
        self.add_css_and_js_file()
        return self.render_page(course, task, submission_id)

    def POST_AUTH(self, course_id, task_id, submission_id):
        """ POST request """
        try:
            self.update_manual_comment_and_grade(submission_id)
        except ManualScoringError as error:
            api_error = APIError(400, {"error": error.get_message()})
            api_error.send()
            return
        except APIError as error:
            error.send()
            return

        return 200, {"status": "success", "text": "Update successfully"}

    def update_manual_comment_and_grade(self, submission_id):
        """ update the grade and comment on db """
        manual_grade, comment, rubric_status = check_manual_scoring_data()

        self.database.submissions.update(
            {"_id": ObjectId(submission_id)},
            {"$set": {"manual_scoring.grade": manual_grade,
                      "manual_scoring.comment": comment,
                      "manual_scoring.rubric_status": rubric_status
                      }
             })

    def render_page(self, course, task, submission_id):
        """ Get all data and display the page """
        rubric_content = self.get_rubric_content()
        problem_id = task.get_problems()[0].get_id()
        submission = self.submission_manager.get_submission(submission_id, user_check=False)
        submission_input = self.submission_manager.get_input_from_submission(submission)
        comment, score, rubric_status = get_manual_scoring_data(submission)

        data = {
            "url": 'manual_scoring',
            "summary": submission_input['custom']['custom_summary_result'],
            "grade": score,
            "language": submission_input['input'][problem_id + '/language'],
            "comment": comment,
            "score": submission_input['grade'],
            "task_name": course.get_task(submission_input['taskid']).get_name(self.user_manager.session_language()),
            "result": submission_input['result'],
            "feedback_result_text": get_submission_result_text(submission_input),
            "problem": submission_input['input'][problem_id],
            "username": submission_input['username'][0],
            "name": self.user_manager.get_user_realname(submission_input['username'][0]),
            "env": task.get_environment(),
            "question_id": problem_id,
            "submission_id": submission_id,
            "rubric_status": rubric_status
        }

        return (
            self.template_helper.get_custom_renderer(base_renderer_path).manual_scoring(
                course, task, rubric_content, data)
        )

    def get_rubric_content(self):
        """ return the content of the rubric depending of the language """
        path = 'inginious/frontend/plugins/manual_scoring/static/json/'
        language_file = {'es': 'rubric_es.json', 'en': 'rubric.json', 'de': 'rubric.json', 'fr': 'rubric.json',
                         'pt': 'rubric.json'}
        current_language = self.user_manager.session_language()
        path = os.path.join(path, language_file[current_language])

        return read_json_file(path)

    def add_css_and_js_file(self):
        if get_use_minify():
            self.template_helper.add_css("/manual_scoring/static/css/manual_scoring.min.css")
            self.template_helper.add_javascript("/manual_scoring/static/js/manual_scoring.min.js")
        else:
            self.template_helper.add_css("/manual_scoring/static/css/manual_scoring.css")
            self.template_helper.add_javascript("/manual_scoring/static/js/code_field.js")
            self.template_helper.add_javascript("/manual_scoring/static/js/message_box.js")
            self.template_helper.add_javascript("/manual_scoring/static/js/rubric.js")
            self.template_helper.add_javascript("/manual_scoring/static/js/manual_scoring_main.js")
