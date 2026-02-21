from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from extensions import db
from model.models import SubjectMember, Tag, Priority, Task
from utils import login_required, parse_date

"""
Task Management Blueprint.
Focuses on individual task creation, status updates, and tag integration.
"""

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    """Adds a new task to a specific subject with optional tags and priorities."""
    user_id = session['user_id']
    memberships = SubjectMember.query.filter_by(user_id=user_id, status='accepted').all()
    user_subjects = [m.subject for m in memberships]

    available_tags = Tag.query.all()
    available_priorities = Priority.query.order_by(Priority.weight.asc()).all()
    
    if request.method == 'POST':
        due_date = parse_date(request.form.get('due_date_str'))
        new_task = Task(
            title=request.form.get('title'),
            description=request.form.get('description'),
            due_date=due_date,
            subject_id=request.form.get('subject_id'),
            user_id=user_id,
            priority_id=request.form.get('priority_id')
        )
        for t_id in request.form.getlist('tag_ids'):
            try:
                tag_obj = db.session.get(Tag, int(t_id)) 
                if tag_obj:
                    new_task.tags.append(tag_obj)
            except (ValueError, TypeError):
                continue
            
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('main.view_subject', subject_id=new_task.subject_id))
        
    return render_template('addtask.html', subjects=user_subjects, tags=available_tags, priorities=available_priorities)
# marks tasks as complete
@tasks_bp.route('/complete_task/<int:task_id>')
@login_required
def complete_task(task_id):
    """Marks a task as completed."""
    task = db.session.get(Task, task_id) or abort(404)
    if task.user_id != session['user_id']:
        flash("Permission denied.")
        return redirect(url_for('main.dashboard'))

    task.status_id = 2
    db.session.commit()
    return redirect(url_for('main.view_subject', subject_id=task.subject_id))