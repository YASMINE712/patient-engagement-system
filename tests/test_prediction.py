import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from health_friend.prediction import blueprint, validate
from health_friend.data_pipeline.train_classifier import binary_target, metrics, cluster_auc_interval
from flask import Flask


class PredictionTests(unittest.TestCase):
    def setUp(self):
        self.values = dict(age=30,gender='female',planned_slot=3,study_day=14,steps_previous_30m=120,action='no_suggestion')
        self.app = Flask(__name__)
        self.app.register_blueprint(blueprint)
        self.client = self.app.test_client()

    def test_finite_bounded_inputs_and_unknown_fields(self):
        for key,value in [('age',True),('age',65),('study_day',1.2),('steps_previous_30m',float('nan')),('action',[]),('gender','unknown')]:
            with self.subTest(key=key,value=value):
                with self.assertRaises(ValueError): validate({**self.values,key:value})
        with self.assertRaises(ValueError): validate({**self.values,'target':1})
        frame = validate({**self.values,'steps_previous_30m':None})
        self.assertTrue(frame.steps_previous_30m.isna().iloc[0])
        self.assertEqual(self.client.post('/predict/run',json={'age':30}).status_code,400)

    def test_missing_artifacts_fail_without_fabricated_output(self):
        with tempfile.TemporaryDirectory() as folder, patch('health_friend.prediction.ROOT',Path(folder)):
            result = self.client.post('/predict/run',json=self.values)
            self.assertEqual(result.status_code,503)
            self.assertNotIn('predicted_steps',result.json)
        self.assertEqual(self.client.get('/predict/figure/private.json').status_code,404)

    def test_saved_models_are_used_for_inference(self):
        import joblib
        import json
        from sklearn.dummy import DummyClassifier, DummyRegressor
        from health_friend.data_pipeline.train_baseline import make_pipeline, FEATURES
        frame = pd.concat([validate(self.values)]*4,ignore_index=True)
        reg = make_pipeline(DummyRegressor(strategy='constant',constant=np.log1p(42))).fit(frame[FEATURES],[0]*4)
        cls = make_pipeline(DummyClassifier(strategy='prior')).fit(frame[FEATURES],[0,1,1,1])
        with tempfile.TemporaryDirectory() as folder, patch('health_friend.prediction.ROOT',Path(folder)):
            root=Path(folder);(root/'artifacts').mkdir();(root/'reports/generated').mkdir(parents=True)
            for name,model in [('heartsteps_activity_model',reg),('heartsteps_activity_classifier',cls)]:
                joblib.dump(model,root/'artifacts'/f'{name}.joblib')
            for name in ['heartsteps_model','heartsteps_classifier']:
                (root/'reports/generated'/f'{name}.json').write_text(json.dumps({'selected_model':'test_fixture'}))
            result=self.client.post('/predict/run',json=self.values)
            self.assertEqual(result.status_code,200)
            self.assertAlmostEqual(result.json['predicted_steps'],42)
            self.assertAlmostEqual(result.json['probability_any_steps'],.75)
            self.assertFalse(result.json['inputs_saved'])

    def test_classification_target_does_not_treat_missing_as_zero(self):
        with self.assertRaises(ValueError): binary_target(pd.DataFrame({'steps_next_30m':[0,np.nan]}))
        np.testing.assert_array_equal(binary_target(pd.DataFrame({'steps_next_30m':[0,1,100]})),[0,1,1])

    def test_metrics_and_cluster_interval(self):
        actual=np.array([0,1,0,1]);prob=np.array([.1,.9,.2,.8])
        result=metrics(actual,prob)
        self.assertEqual(result['roc_auc'],1)
        self.assertEqual(result['confusion_matrix'],[[2,0],[0,2]])
        interval=cluster_auc_interval(actual,prob,np.array([1,1,2,2]),repeats=20)
        self.assertEqual(interval['low'],1)
        self.assertEqual(interval['valid_resamples'],20)
