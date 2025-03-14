from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
views = Blueprint('views', __name__)

@views.route('/')