"""Module to evaluate model performances on a new patient"""

import pandas as pd
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import pathlib
import pickle
import tensorflow as tf
import logging
from keras.models import model_from_json

tf.compat.v1.logging.set_verbosity(0)
tf.get_logger().setLevel('CRITICAL')
logger = logging.getLogger('tensorflow')
logger.setLevel(logging.CRITICAL)

#hi

class ModelEvaluator():
    """Class to evaluate pre-trained model"""

    def __init__(self, features_df: pd.DataFrame, model_path, out_path):
        self.data = features_df
        self.model_path = model_path
        self.model_json_path = os.path.join(model_path,'model.json')
        self.model_weights_path= os.path.join(model_path,'model.h5')
        self.scaler_path = os.path.join(model_path,'scaler.pkl')
        self.out_path = out_path

    def preprocess(self,):
        """Remove non-relevant features
        and some other useful preprocesing."""

        self.data['PatientAge'] = self.data['PatientAge'].str[1:-1].astype(int)
        self.data['PatientSex'] = self.data['PatientSex'].map({'M': 0, 'F': 1})

        data_pre_scaled = self.data
        acc_number = data_pre_scaled.pop('AccessionNumber')
        cov_label =  data_pre_scaled.pop('COVlabel')

        data_copy = data_pre_scaled

        scaler = pickle.load(open(self.scaler_path, 'rb'))
        scaled = scaler.transform(data_pre_scaled)
        data_scaled = pd.DataFrame(scaler.transform(scaled), columns=data_pre_scaled.columns)



        a_file = open(os.path.join(self.model_path, 'features.txt'), "r")

        lines = a_file.read()
        cols_to_keep = lines.splitlines()
        data_scaled = data_scaled[cols_to_keep + ['PatientSex', 'PatientAge']]
        data_copy['AccessionNumber'] = acc_number
        data_copy = data_copy[cols_to_keep]

        #write csv file of selected radiomic features
        data_copy.to_csv(os.path.join(pathlib.Path(self.out_path).parent, 'radiomic_selected.csv'), index=False)
        self.data = data_scaled
        self.accnumber = acc_number
        self.covlabel = cov_label


    def run(self):
        """Execute main method of ModelEvaluator class"""

        tf.keras.backend.clear_session()

        # load json and create model
        json_file = open(self.model_json_path, 'r', encoding='utf-8')
        loaded_model_json = json_file.read()
        json_file.close()

        loaded_model = model_from_json(loaded_model_json)
        loaded_model.load_weights(self.model_weights_path)

        # evaluate loaded model on test data
        loss = tf.keras.losses.BinaryCrossentropy(from_logits=True)
        optimizer = tf.keras.optimizers.Nadam()
        loaded_model.compile(optimizer=optimizer,
            loss=loss,
            metrics=['accuracy'])

        tf.keras.backend.clear_session()

        predictions = loaded_model.predict(self.data)
        predictions = predictions[:,0]

        covid_prob = [ round(x,3) for x in predictions]
        pred_labels = [0 if pr<0.5 else 1 for pr in predictions]

        df_to_out = pd.DataFrame({'AccessionNumber': self.accnumber,
                                  'CovidProbability': covid_prob,
                                  'PredictedLabel': pred_labels,
                                  'TrueLabel':self.covlabel})
        df_to_out.to_csv(self.out_path, index=False, sep='\t')

        return df_to_out


if __name__=='__main__':
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
    m = ModelEvaluator(features_df=pd.read_csv("/home/kobayashi/Scrivania/andreasala/results/radiomic_features.csv", sep='\t'),
                        model_path="/home/kobayashi/Scrivania/andreasala/covid-classifier/src/covidlib/model",
                        out_path="/home/kobayashi/Scrivania/andreasala/results/evaluation_results.csv")
    m.preprocess()
    m.run()
