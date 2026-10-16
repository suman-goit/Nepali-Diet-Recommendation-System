import logging
import warnings

from django.apps import AppConfig
from django.db.models.signals import post_migrate

logger = logging.getLogger(__name__)


def bootstrap_data(sender, **kwargs):
    """
    Runs after `python manage.py migrate`.

    On a fresh deploy (e.g. Render, where the disk/database starts empty) this:
      1. seeds the Food table from data/food_table_clean.csv if it is empty
      2. retrains the Decision Tree if the saved model is missing or was built
         with a different scikit-learn version than the one installed.

    Wrapped in try/except so a problem here never blocks the server from starting.
    """
    from django.core.management import call_command

    try:
        from .models import Food

        if not Food.objects.exists():
            call_command("seed_data")
    except Exception:
        logger.exception("Automatic food seeding failed")
        return

    try:
        import joblib
        from .services import ml_service

        needs_training = True
        if ml_service.MODEL_PATH.exists():
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("error")  # version mismatch warning -> retrain
                    joblib.load(ml_service.MODEL_PATH)
                needs_training = False
            except Exception:
                needs_training = True

        if needs_training:
            call_command("train_decision_tree")
    except Exception:
        logger.exception("Automatic model training failed")


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        post_migrate.connect(bootstrap_data, sender=self)
