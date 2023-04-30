"""Module to evaluate model performances on a new patient"""
import pathlib
import pickle
import logging
import os
import tensorflow as tf
from keras.models import model_from_json
import pandas as pd

tf.compat.v1.logging.set_verbosity(0)
tf.get_logger().setLevel('CRITICAL')
logger = logging.getLogger('tensorflow')
logger.setLevel(logging.CRITICAL)

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

class ModelEvaluator():
    """Class to evaluate pre-trained model"""

    def __init__(self, features_df: pd.DataFrame, model_path, out_path, ad):
    def __init__(self, features_df: pd.DataFrame, model_path, out_path, ad):
        """Constructor for the ModelEvaluator Class.
        :param features_df: pandas.DataFrame containing the extracted radiomic features
        :param model_path: path to the model directory
        :param out_path: path where to save the csv with evaluation results
        :param ad: Analysis date and time
        """
        self.data = features_df
        self.model_path = model_path
        self.model_json_path = os.path.join(model_path, 'model.json')
        self.model_weights_path = os.path.join(model_path, 'model.h5')
        self.scaler_path = os.path.join(model_path, 'scaler.pkl')
        self.model_json_path = os.path.join(model_path, 'model.json')
        self.model_weights_path = os.path.join(model_path, 'model.h5')
        self.scaler_path = os.path.join(model_path, 'scaler.pkl')
        self.out_path = out_path
        self.ad = ad
        self.ad = ad

    def preprocess(self,):
        """Remove non-relevant features
        and some other useful preprocesing."""
        try:
            self.data['PatientAge'].replace('Y', '', inplace=True, regex=True)
        except:
            pass
        self.data['PatientAge'] = self.data['PatientAge'].astype(int)
        try:
            self.data['PatientAge'].replace('Y', '', inplace=True, regex=True)
        except:
            pass
        self.data['PatientAge'] = self.data['PatientAge'].astype(int)
        self.data['PatientSex'] = self.data['PatientSex'].map({'M': 0, 'F': 1})

        data_pre_scaled = self.data
        acc_number = data_pre_scaled.pop('AccessionNumber')
        cov_label = data_pre_scaled.pop('PatientTag')
        data_pre_scaled.pop('Series Description')
        data_pre_scaled.pop('Analysis Date')
        
        data_pre_scaled.pop('Tag')
        data_pre_scaled.pop('Manufacturer')
        data_pre_scaled.pop('Scanner Model')
        data_pre_scaled.pop('mAs')
        data_pre_scaled.pop('kVp')
        data_pre_scaled.pop('pitch')
        data_pre_scaled.pop('Single Collimation')
        data_pre_scaled.pop('Total Collimation')
        data_pre_scaled.pop('CTDI')
        data_pre_scaled.pop('Slice Thickness')
        data_pre_scaled.pop('Slice Increment')
        data_pre_scaled.pop('Kernel')
        data_pre_scaled.pop('Strength')
        data_pre_scaled.pop('Reconstruction Diameter')

        data_copy = data_pre_scaled

        scaler = pickle.load(open(self.scaler_path, 'rb'))
        scaled = scaler.transform(data_pre_scaled)
        data_scaled = pd.DataFrame(scaler.transform(scaled), columns=data_pre_scaled.columns)

        with open(os.path.join(self.model_path, 'features.txt'),
            "r", encoding='utf-8') as a_file:
            lines = a_file.read()
            cols_to_keep = lines.splitlines()

        model_name = cols_to_keep.pop(0)
        data_scaled = data_scaled[cols_to_keep + ['PatientSex', 'PatientAge']]
        data_copy['AccessionNumber'] = acc_number
        data_copy = data_copy[cols_to_keep]

        #write csv file of selected radiomic features
        data_copy.to_csv(os.path.join(pathlib.Path(self.out_path).parent, 'radiomic_selected.csv'), index=False)
        self.data = data_scaled
        self.accnumber = acc_number
        self.covlabel = cov_label
        self.model_name = model_name


    def run(self):
        """Execute main method of ModelEvaluator class"""

        tf.keras.backend.clear_session()

        # load json and create model
        with open(self.model_json_path, 'r', encoding='utf-8') as json_file:
            loaded_model_json = json_file.read()


        loaded_model = model_from_json(loaded_model_json)
        loaded_model.load_weights(self.model_weights_path)

        # evaluate loaded model on test data
        loss = tf.keras.losses.BinaryCrossentropy(from_logits=True)
        optimizer = tf.keras.optimizers.Nadam()
        loaded_model.compile(optimizer=optimizer,
                             loss = loss,
                             metrics = ['accuracy'])
                             loss = loss,
                             metrics = ['accuracy'])

        tf.keras.backend.clear_session()

        predictions = loaded_model.predict(self.data)
        predictions = predictions[:, 0]

        covid_prob = [round(x, 3) for x in predictions]
        pred_labels = [0 if pr < 0.5 else 1 for pr in predictions]

        df_to_out = pd.DataFrame({'AccessionNumber': self.accnumber,
                                  'AnalysisDate': self.ad,
                                  'AnalysisDate': self.ad,
                                  'ModelName': self.model_name,
                                  'CovidProbability': covid_prob,
                                  'PredictedLabel': pred_labels,
                                  'TrueLabel':self.covlabel})
        df_to_out.to_csv(self.out_path, index=False, sep='\t')

        return df_to_out
