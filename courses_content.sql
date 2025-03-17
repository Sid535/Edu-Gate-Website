-- 1. Users Table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,  -- Added username
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('student', 'teacher', 'admin') NOT NULL DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Password Resets Table
CREATE TABLE password_resets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (user_id)
);
CREATE INDEX idx_password_resets_token ON password_resets(token);

-- 3. Courses Table
CREATE TABLE courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by INT,  -- Teacher/admin who created the course
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 4. Enrollments Table
CREATE TABLE enrollments (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    UNIQUE (student_id, course_id)  -- Prevent duplicate enrollments
);

-- 5. Subjects Table
CREATE TABLE subjects (
    subject_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT,
    subject_name VARCHAR(255) NOT NULL,
    created_by INT,  -- Teacher/admin who created the subject
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 6. Materials Table (with improved file_url)
CREATE TABLE materials (
    material_id INT AUTO_INCREMENT PRIMARY KEY,
    subject_id INT,
    title VARCHAR(255) NOT NULL,
    material_type ENUM('PDF', 'Video', 'Link') NOT NULL,
    file_url TEXT,  -- Changed to TEXT for long URLs
    uploaded_by INT,  -- Teacher who uploaded
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 7. Tests Table
CREATE TABLE tests (
    test_id INT AUTO_INCREMENT PRIMARY KEY,
    subject_id INT,
    test_name VARCHAR(255) NOT NULL,
    test_date DATE,
    max_score DECIMAL(5,2) NOT NULL,  -- Allows decimal scores
    created_by INT,  -- Teacher who created
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 8. Questions Table
CREATE TABLE questions (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    test_id INT NOT NULL,
    question_text TEXT NOT NULL,
    question_type ENUM('Multiple Choice', 'True/False', 'Short Answer', 'Essay') NOT NULL,
    points DECIMAL(5,2) NOT NULL DEFAULT 1.00,  -- Decimal points
    FOREIGN KEY (test_id) REFERENCES tests(test_id) ON DELETE CASCADE
);

-- 9. Answer Options Table
CREATE TABLE answer_options (
    option_id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
);
-- 10. Test Attempts Table
CREATE TABLE test_attempts (
    attempt_id INT AUTO_INCREMENT PRIMARY KEY,
    test_id INT NOT NULL,
    student_id INT NOT NULL,
    attempt_number INT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    is_completed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (test_id) REFERENCES tests(test_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (test_id, student_id, attempt_number)
);

-- 11. Test Results Table (with decimal scoring)
CREATE TABLE test_results (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    test_id INT,
    student_id INT,
    attempt_id INT,
    score DECIMAL(5,2) NOT NULL,  -- Changed to decimal
    result_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (test_id) REFERENCES tests(test_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (attempt_id) REFERENCES test_attempts(attempt_id)
);

-- 12. Student Answers Table
CREATE TABLE student_answers (
    answer_id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL,
    student_id INT NOT NULL,
    attempt_id INT NOT NULL,
    selected_option_id INT,
    text_answer TEXT,
    is_correct BOOLEAN,
    points_awarded DECIMAL(5,2),
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (attempt_id) REFERENCES test_attempts(attempt_id) ON DELETE CASCADE,
    FOREIGN KEY (selected_option_id) REFERENCES answer_options(option_id) ON DELETE SET NULL
);