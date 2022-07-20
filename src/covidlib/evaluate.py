"""Module to evaluate model performances on a new patient"""

import pandas as pd
import os
import pickle
import tensorflow as tf
from keras.models import model_from_json


tf.compat.v1.logging.set_verbosity(0)



class ModelEvaluator():
    """Class to evaluate pre-trained model"""

    def __init__(self, features_df: pd.DataFrame, model_path, out_path):
        self.data = features_df
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

        scaler = pickle.load(open(self.scaler_path, 'rb'))
        scaled = scaler.transform(data_pre_scaled)
        data_scaled = pd.DataFrame(scaler.transform(scaled), columns=data_pre_scaled.columns)


        cols_to_drop = ['Acquisition Date', 'Voxel size ISO', '90Percentile_5', 'Energy_5',
                        'Entropy_5', 'InterquartileRange_5',
                        'Kurtosis_5', 'Maximum_5', 'MeanAbsoluteDeviation_5',
                        'Mean_5', 'Median_5',
                        'RobustMeanAbsoluteDeviation_5', 'RootMeanSquared_5', 'TotalEnergy_5',
                        'Uniformity_5', 'Autocorrelation_5', 'ClusterProminence_5','ClusterShade_5',
                        'ClusterTendency_5', 'Contrast_5', 'Correlation_5' ,'DifferenceAverage_5',
                        'DifferenceEntropy_5' ,'Id_5', 'Idm_5' ,'Idmn_5' ,'Idn_5',
                        'Imc1_5', 'Imc2_5','InverseVariance_5', 'JointAverage_5',
                        'JointEnergy_5', 'MCC_5','MaximumProbability_5' ,'SumAverage_5',
                        'SumEntropy_5' ,'SumSquares_5',
                        'Autocorrelation_25' ,'ClusterProminence_25', 'ClusterShade_25',
                        'ClusterTendency_25', 'Contrast_25' ,'Correlation_25',
                        'DifferenceAverage_25' ,'DifferenceEntropy_25', 'DifferenceVariance_25',
                        'Id_25' ,'Idm_25', 'Idmn_25', 'Idn_25', 'Imc1_25' ,'JointAverage_25',
                        'JointEnergy_25', 'JointEntropy_25' ,'MCC_25', 'MaximumProbability_25',
                        'SumAverage_25', 'SumEntropy_25' ,'SumSquares_25' ,'Autocorrelation_50',
                        'ClusterTendency_50' ,'Contrast_50' ,'Correlation_50',
                        'DifferenceAverage_50', 'DifferenceEntropy_50', 'DifferenceVariance_50',
                        'Id_50' ,'Idm_50', 'Idmn_50', 'Idn_50' ,'Imc1_50' ,'Imc2_50',
                        'InverseVariance_50', 'JointAverage_50','JointEnergy_50' ,'JointEntropy_50',
                        'MCC_50' ,'MaximumProbability_50','SumAverage_50' ,'SumEntropy_50',
                        'SumSquares_50', 'GrayLevelVariance_25', 'HighGrayLevelZoneEmphasis_25',
                        'LargeAreaEmphasis_25' ,'LargeAreaHighGrayLevelEmphasis_25',
                        'LargeAreaLowGrayLevelEmphasis_25' ,'SizeZoneNonUniformity_25',
                        'SizeZoneNonUniformityNormalized_25' ,'SmallAreaEmphasis_25',
                        'SmallAreaHighGrayLevelEmphasis_25' ,'SmallAreaLowGrayLevelEmphasis_25',
                        'ZoneEntropy_25' ,'ZoneVariance_25' ,'GrayLevelNonUniformity_100',
                        'GrayLevelNonUniformityNormalized_100' ,'GrayLevelVariance_100',
                        'HighGrayLevelZoneEmphasis_100', 'LargeAreaEmphasis_100',
                        'LargeAreaLowGrayLevelEmphasis_100' ,'LowGrayLevelZoneEmphasis_100',
                        'SizeZoneNonUniformity_100' ,'SmallAreaEmphasis_100',
                        'SmallAreaHighGrayLevelEmphasis_100', 'ZoneEntropy_100' ,'ZoneVariance_100',
                        'GrayLevelNonUniformity_200' ,'GrayLevelNonUniformityNormalized_200',
                        'GrayLevelVariance_200', 'HighGrayLevelZoneEmphasis_200',
                        'LargeAreaEmphasis_200', 'LargeAreaLowGrayLevelEmphasis_200',
                        'LowGrayLevelZoneEmphasis_200' ,'SizeZoneNonUniformity_200',
                        'SizeZoneNonUniformityNormalized_200', 'SmallAreaEmphasis_200',
                        'SmallAreaLowGrayLevelEmphasis_200' ,'ZoneEntropy_200' ,'ZoneVariance_200']

        data_scaled = data_scaled.drop(cols_to_drop, axis=1, )
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
    m = ModelEvaluator(features_df=pd.read_csv("/home/kobayashi/Scrivania/andreasala/results/radiomics_features.csv", sep='\t'),
                        model_path="/home/kobayashi/Scrivania/andreasala/covid-classifier/src/covidlib/model",
                        out_path="/home/kobayashi/Scrivania/andreasala/results/evaluation_results.csv")
    m.preprocess()
    m.run()