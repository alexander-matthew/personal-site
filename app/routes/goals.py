from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Category, Goal, ProgressLog

bp = Blueprint('goals', __name__, url_prefix='/projects/goals')


# ============================================================================
# Authentication Routes
# ============================================================================

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for('goals.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        errors = []
        if len(username) < 3:
            errors.append('Username must be at least 3 characters')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters')
        if password != confirm_password:
            errors.append('Passwords do not match')
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('goals/register.html', username=username)

        # Create user
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Create preset categories for new user
        Category.create_presets_for_user(user.id)
        db.session.commit()

        login_user(user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('goals.dashboard'))

    return render_template('goals/register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('goals.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('goals.dashboard'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('goals/login.html')


@bp.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('goals.login'))


# ============================================================================
# Dashboard Routes
# ============================================================================

@bp.route('/')
@login_required
def dashboard():
    """Main dashboard - Today's focus view."""
    today = datetime.now(timezone.utc).date()

    # Get user's goals organized by type
    daily_goals = Goal.query.filter_by(
        user_id=current_user.id,
        frequency='daily'
    ).filter(Goal.completed_at.is_(None)).all()

    # Check which daily goals were completed today
    for goal in daily_goals:
        goal.completed_today = ProgressLog.query.filter(
            ProgressLog.goal_id == goal.id,
            db.func.date(ProgressLog.logged_at) == today
        ).first() is not None

    # Upcoming deadlines (next 7 days)
    week_from_now = today + timedelta(days=7)
    upcoming_goals = Goal.query.filter(
        Goal.user_id == current_user.id,
        Goal.deadline.isnot(None),
        Goal.deadline <= week_from_now,
        Goal.completed_at.is_(None)
    ).order_by(Goal.deadline).all()

    # Active streaks (streak-type goals with current streak > 0)
    streak_goals = Goal.query.filter_by(
        user_id=current_user.id,
        goal_type='streak'
    ).filter(Goal.completed_at.is_(None)).all()

    # Calculate stats
    total_goals = Goal.query.filter_by(user_id=current_user.id).count()
    completed_goals = Goal.query.filter(
        Goal.user_id == current_user.id,
        Goal.completed_at.isnot(None)
    ).count()

    # Categories for display
    categories = Category.query.filter_by(user_id=current_user.id).all()

    return render_template(
        'goals/dashboard.html',
        daily_goals=daily_goals,
        upcoming_goals=upcoming_goals,
        streak_goals=streak_goals,
        total_goals=total_goals,
        completed_goals=completed_goals,
        categories=categories,
        today=today
    )


@bp.route('/all')
@login_required
def all_goals():
    """View all goals grouped by category."""
    categories = Category.query.filter_by(user_id=current_user.id).all()

    # Get goals for each category
    for category in categories:
        category.active_goals = Goal.query.filter_by(
            user_id=current_user.id,
            category_id=category.id
        ).filter(Goal.completed_at.is_(None)).all()

    # Uncategorized goals
    uncategorized = Goal.query.filter_by(
        user_id=current_user.id,
        category_id=None
    ).filter(Goal.completed_at.is_(None)).all()

    return render_template(
        'goals/all_goals.html',
        categories=categories,
        uncategorized=uncategorized
    )


# ============================================================================
# Goal CRUD Routes
# ============================================================================

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_goal():
    """Create a new goal."""
    categories = Category.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':
        # Validate category belongs to current user
        category_id = None
        if request.form.get('category_id'):
            cat = Category.query.filter_by(
                id=int(request.form.get('category_id')),
                user_id=current_user.id
            ).first()
            category_id = cat.id if cat else None

        goal = Goal(
            user_id=current_user.id,
            title=request.form.get('title', '').strip(),
            description=request.form.get('description', '').strip() or None,
            goal_type=request.form.get('goal_type', 'one_time'),
            progress_type=request.form.get('progress_type', 'binary'),
            target_value=int(request.form.get('target_value', 1) or 1),
            frequency=request.form.get('frequency') or None,
            priority=request.form.get('priority', 'normal'),
            category_id=category_id
        )

        # Parse deadline if provided
        deadline_str = request.form.get('deadline', '').strip()
        if deadline_str:
            try:
                goal.deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        db.session.add(goal)
        db.session.commit()

        flash('Goal created!', 'success')
        return redirect(url_for('goals.dashboard'))

    return render_template('goals/new_goal.html', categories=categories)


@bp.route('/<int:goal_id>')
@login_required
def view_goal(goal_id):
    """View a single goal with progress history."""
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    today = datetime.now(timezone.utc).date()

    # Get recent progress logs
    logs = ProgressLog.query.filter_by(goal_id=goal.id).order_by(
        ProgressLog.logged_at.desc()
    ).limit(30).all()

    return render_template('goals/view_goal.html', goal=goal, logs=logs, today=today)


@bp.route('/<int:goal_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_goal(goal_id):
    """Edit an existing goal."""
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    categories = Category.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':
        # Validate category belongs to current user
        category_id = None
        if request.form.get('category_id'):
            cat = Category.query.filter_by(
                id=int(request.form.get('category_id')),
                user_id=current_user.id
            ).first()
            category_id = cat.id if cat else None

        goal.title = request.form.get('title', '').strip()
        goal.description = request.form.get('description', '').strip() or None
        goal.goal_type = request.form.get('goal_type', 'one_time')
        goal.progress_type = request.form.get('progress_type', 'binary')
        goal.target_value = int(request.form.get('target_value', 1) or 1)
        goal.frequency = request.form.get('frequency') or None
        goal.priority = request.form.get('priority', 'normal')
        goal.category_id = category_id

        deadline_str = request.form.get('deadline', '').strip()
        if deadline_str:
            try:
                goal.deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                goal.deadline = None
        else:
            goal.deadline = None

        db.session.commit()
        flash('Goal updated!', 'success')
        return redirect(url_for('goals.view_goal', goal_id=goal.id))

    return render_template('goals/edit_goal.html', goal=goal, categories=categories)


@bp.route('/<int:goal_id>/delete', methods=['POST'])
@login_required
def delete_goal(goal_id):
    """Delete a goal."""
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    db.session.delete(goal)
    db.session.commit()
    flash('Goal deleted', 'info')
    return redirect(url_for('goals.dashboard'))


# ============================================================================
# Progress Tracking API
# ============================================================================

@bp.route('/api/log-progress', methods=['POST'])
@login_required
def log_progress():
    """Log progress for a goal (AJAX endpoint)."""
    data = request.get_json()
    goal_id = data.get('goal_id')
    value = data.get('value', 1)

    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    if not goal:
        return jsonify({'error': 'Goal not found'}), 404

    # Create progress log
    log = ProgressLog(goal_id=goal.id, value=value)
    db.session.add(log)

    # Update goal progress
    if goal.progress_type == 'percentage':
        goal.current_value = min(goal.target_value, goal.current_value + value)
        if goal.current_value >= goal.target_value:
            goal.completed_at = datetime.now(timezone.utc)
    elif goal.goal_type == 'one_time':
        goal.completed_at = datetime.now(timezone.utc)

    db.session.commit()

    return jsonify({
        'success': True,
        'current_value': goal.current_value,
        'target_value': goal.target_value,
        'progress_percent': goal.progress_percent,
        'is_completed': goal.is_completed
    })


@bp.route('/api/toggle-daily', methods=['POST'])
@login_required
def toggle_daily():
    """Toggle daily goal completion for today (AJAX endpoint)."""
    data = request.get_json()
    goal_id = data.get('goal_id')
    today = datetime.now(timezone.utc).date()

    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    if not goal:
        return jsonify({'error': 'Goal not found'}), 404

    # Check if already logged today
    existing_log = ProgressLog.query.filter(
        ProgressLog.goal_id == goal.id,
        db.func.date(ProgressLog.logged_at) == today
    ).first()

    if existing_log:
        # Remove today's log
        db.session.delete(existing_log)
        completed_today = False
    else:
        # Add today's log
        log = ProgressLog(goal_id=goal.id, value=1)
        db.session.add(log)
        completed_today = True

    db.session.commit()

    return jsonify({
        'success': True,
        'completed_today': completed_today,
        'current_streak': goal.current_streak
    })


# ============================================================================
# Category Management
# ============================================================================

@bp.route('/categories')
@login_required
def categories():
    """View and manage categories."""
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('goals/categories.html', categories=categories)


@bp.route('/categories/new', methods=['POST'])
@login_required
def new_category():
    """Create a new category."""
    name = request.form.get('name', '').strip()
    color = request.form.get('color', '#60a5fa')

    if name:
        category = Category(
            user_id=current_user.id,
            name=name,
            color=color,
            is_preset=False
        )
        db.session.add(category)
        db.session.commit()
        flash(f'Category "{name}" created!', 'success')

    return redirect(url_for('goals.categories'))


@bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    """Delete a category (goals become uncategorized)."""
    category = Category.query.filter_by(
        id=category_id,
        user_id=current_user.id
    ).first_or_404()

    # Remove category from goals (don't delete the goals)
    Goal.query.filter_by(category_id=category.id).update({'category_id': None})

    db.session.delete(category)
    db.session.commit()
    flash(f'Category "{category.name}" deleted', 'info')

    return redirect(url_for('goals.categories'))
