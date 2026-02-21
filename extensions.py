from flask_sqlalchemy import SQLAlchemy

"""
standardising extensions for W Notes+
preventing circular dependencies between models and blueprints
"""

#to interact with DB without circular imports
db = SQLAlchemy()