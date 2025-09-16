import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from models import db, Post
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db.init_app(app)

# Run the scheduler with a timezone; naive datetimes are treated as local
scheduler = BackgroundScheduler()
scheduler.start()


def schedule_job(post: Post):
    """(Re)schedule a post's publish job."""
    scheduler.add_job(
        func=publish_post,
        trigger='date',
        run_date=post.schedule_time,
        args=[post.id],
        id=f'post_{post.id}',          # stable id to update/remove later
        replace_existing=True,
        misfire_grace_time=120         # if server was down briefly
    )


# --------- PUBLISH ----------
def publish_post(post_id: int):
    """Mark a post published (called by APScheduler)."""
    # Background thread -> need an app context
    with app.app_context():
        post = Post.query.get(post_id)
        if not post:
            print(f'[publish_post] Post {post_id} not found')
            return
        if post.published:
            print(f'[publish_post] Post {post_id} already published')
            return

        # Mark the post as published and set the published_at time
        post.published = True
        post.published_at = datetime.now()  # Set the actual publish time
        db.session.commit()
        print(f'[publish_post] Published post {post.id}: {post.text}')


# --------- ROUTES ----------
@app.route('/')
def index():
    # Only UNPUBLISHED, future-dated posts in "Scheduled"
    posts = (Post.query
             .filter_by(published=False)
             .order_by(Post.schedule_time.asc())
             .all())
    return render_template('index.html', posts=posts)

@app.route('/preview')
def preview():
    # Published posts shown here
    posts = (Post.query
             .filter_by(published=True)
             .order_by(Post.schedule_time.desc())
             .all())
    return render_template('preview.html', posts=posts)

@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    if request.method == 'POST':
        text = request.form['text'].strip()
        schedule_time_str = request.form['schedule_time']
        # datetime-local => 2025-09-15T17:48
        try:
            schedule_time = datetime.strptime(schedule_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date/time format', 'danger')
            return render_template('schedule.html', now=_now_for_input())

        # Server-side guard: no past times
        if schedule_time <= datetime.now():
            flash('You cannot schedule a post in the past.', 'danger')
            return render_template('schedule.html', now=_now_for_input())

        file = request.files.get('image')
        if not file or file.filename == '':
            flash('Please choose an image.', 'danger')
            return render_template('schedule.html', now=_now_for_input())

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        new_post = Post(text=text, image=filename, schedule_time=schedule_time)
        db.session.add(new_post)
        db.session.commit()

        # Schedule the job
        schedule_job(new_post)
        flash('Post scheduled successfully!', 'success')
        return redirect(url_for('index'))

    # GET
    return render_template('schedule.html', now=_now_for_input())

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit(post_id):
    post = Post.query.get_or_404(post_id)
    if post.published:
        flash('Published posts cannot be edited.', 'warning')
        return redirect(url_for('preview'))

    if request.method == 'POST':
        post.text = request.form['text'].strip()

        schedule_time_str = request.form['schedule_time']
        try:
            new_time = datetime.strptime(schedule_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date/time format', 'danger')
            return render_template('edit.html', post=post, min_dt=_now_for_input())

        if new_time <= datetime.now():
            flash('You cannot schedule a post in the past.', 'danger')
            return render_template('edit.html', post=post, min_dt=_now_for_input())

        # handle optional new image
        file = request.files.get('image')
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            post.image = filename

        post.schedule_time = new_time
        db.session.commit()

        # Reschedule the job
        schedule_job(post)
        flash('Post updated.', 'success')
        return redirect(url_for('index'))

    return render_template('edit.html', post=post, min_dt=_now_for_input())

@app.route('/delete/<int:post_id>', methods=['POST'])
def delete(post_id):
    post = Post.query.get_or_404(post_id)

    # If not yet published, remove the scheduled job
    if not post.published:
        try:
            scheduler.remove_job(f'post_{post.id}')
        except JobLookupError:
            pass

    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'success')

    return redirect(url_for('index' if not post.published else 'preview'))


# --------- helpers ----------
def _now_for_input():
    """Return current time formatted for datetime-local min/value."""
    return datetime.now().strftime('%Y-%m-%dT%H:%M')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
