import unittest
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from health_friend.data_pipeline.train_baseline import make_pipeline, evaluate, FEATURES


class TrainingTests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame({'participant_id': [1, 1, 2, 2], 'age': [20, 30, 40, 50],
                             'planned_slot': [1, 2, 3, 4], 'study_day': [1, 1, 2, 2],
                             'steps_previous_30m': [0, 20, 40, 60], 'gender': ['female'] * 4,
                             'action': ['walking', 'no_suggestion', 'walking', 'no_suggestion'],
                             'steps_next_30m': [5, 20, 30, 40]})

    def test_preprocessing_fitted_only_on_training_values(self):
        train = self.frame()
        model = make_pipeline(Ridge())
        model.fit(train[FEATURES], np.log1p(train['steps_next_30m']))
        imputer = model.named_steps['preprocess'].named_transformers_['numeric'].named_steps['impute']
        self.assertEqual(imputer.statistics_[0], 35)
        before = imputer.statistics_.copy()
        future = train.copy()
        future['age'] = [100, 110, 115, 120]
        future['gender'] = 'unseen_category'
        result = evaluate(model, future)
        np.testing.assert_array_equal(imputer.statistics_, before)
        self.assertTrue(np.isfinite(result['mae_steps']))

    def test_missing_prediction_inputs_handled(self):
        frame = self.frame()
        model = make_pipeline(Ridge()).fit(frame[FEATURES], np.log1p(frame['steps_next_30m']))
        frame['steps_previous_30m'] = np.nan
        prediction = model.predict(frame[FEATURES])
        self.assertTrue(np.isfinite(prediction).all())
