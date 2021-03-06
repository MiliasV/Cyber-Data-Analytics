from __future__ import division
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, GradientBoostingClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import accuracy_score, average_precision_score, f1_score, recall_score, roc_auc_score, roc_curve, auc
from sklearn.neighbors import KNeighborsClassifier
from sklearn import decomposition, tree, preprocessing
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
import operator
import os

plt.rc('xtick', labelsize=20)
plt.rc('ytick', labelsize=20)

data_path = os.path.join('..', 'datasets', 'data_for_student_case.csv')
columns = ["txid", "bookingdate", "issuercountrycode", "txvariantcode", "card_issuer_identifier",
           "amount", "currencycode", "shoppercountrycode", "shopperinteraction", "simple_journal",
           "cardverificationcodesupplied", "cvcresponsecode", "creationdate", "accountcode", "mail_id",
           "ip_id", "card_id"]

selected_features = ["txid", "issuercountrycode", "txvariantcode", "card_issuer_identifier",
                    "amount", "currencycode", "shoppercountrycode", "shopperinteraction", "simple_journal",
                    "cardverificationcodesupplied", "cvcresponsecode", "accountcode", "creationdate_hour",
                     "creationdate_dayofweek",'creationdate_month','creationdate_dayofmonth',  "card_id", "ip_id", "mail_id"]

selected_dummy_features = [ "issuercountrycode", "txvariantcode", "card_issuer_identifier",
                                 "amount", "currencycode", "shoppercountrycode", "shopperinteraction", "simple_journal",
                                 "cardverificationcodesupplied", "cvcresponsecode", "accountcode",
                                "creationdate_hour", "creationdate_dayofweek",'creationdate_month', 'creationdate_dayofmonth']

label = "simple_journal"
features_for_convertion = ["issuercountrycode", "txvariantcode", "shopperinteraction"]


class Fraud:
    def __init__(self):
        self.load_data()
        #self.run()

    def load_data(self):
        # Read from csv
        print("Reading from file")
        self.df = pd.read_csv(data_path, skip_blank_lines=True)
        print("\tFinished!!!")

        print("Pre-processing.")
        # Rename a column
        self.df.rename(columns={'bin': 'card_issuer_identifier'}, inplace=True)
        # Delete rows with null values for card_issuer_identifier
        self.df = self.df[pd.notnull(self.df.card_issuer_identifier)]
        # self.df = self.df[self.df.simple_journal != "Refused"]

        # Change data types of some columns
        #self.df["bookingdate"].apply(self.string_to_timestamp)
        self.df["card_issuer_identifier"].apply(float)
        self.df["amount"].apply(lambda x: float(x)/100)
        self.df['creationdate'] = pd.to_datetime(self.df.creationdate)
        self.df['creationdate_hour'] = self.df['creationdate'].map(lambda x: x.hour)
        self.df['creationdate_dayofweek'] = self.df['creationdate'].map(lambda x: x.weekday())
        self.df['creationdate_dayofmonth'] = self.df['creationdate'].map(lambda x: x.day)
        self.df['creationdate_month'] = self.df['creationdate'].map(lambda x: x.month)
        print("\tFinished!!")

    @staticmethod
    def get_records_and_labels(df, columns):
        return df[columns].values, df["simple_journal"].values

    # Output: dataframe with selected features
    def get_selected_features(self, feature_list):
        return self.df[feature_list]

    # Output format: {"US": 112, ...}
    def total_per_country(self):
         result = self.df["issuercountrycode"].value_counts().to_dict()
         #result.to_csv(path=path,index_label=["issuercountrycode","transaction_count"],index=True)
         return result



    # Output: dictionary
    def total_per_cardtype(self):
        result = self.df["txvariantcode"].value_counts().to_dict()
        return result

    def total_per_day_week(self):
        result = self.df["creationdate_dayofweek"].value_counts().to_dict()
        return result

    def total_per_day_month(self):
        result = self.df["creationdate_dayofmonth"].value_counts().to_dict()
        return result

    def total_per_day(self):
        result = self.df["creationdate_dayofweek"].value_counts().to_dict()
        return result

    def total_per_hour(self):
        result = self.df["creationdate_hour"].value_counts().to_dict()
        return result

    def total_per_cardid(self):
        result = self.df["card_id"].value_counts().to_dict()
        return result

    # Output: dataframe that contains only the "category"
    def filter_records(self, category):
        result = self.df.loc[self.df["simple_journal"] == category]
        return result


    def plot_data_balance(self):
        objects = tuple(self.df["simple_journal"].unique())
        y_pos = np.arange(len(objects))
        num_chargeback = self.df.loc[self.df["simple_journal"] == "Chargeback"].shape[0]
        print num_chargeback
        num_refused = self.df.loc[self.df["simple_journal"] == "Refused"].shape[0]
        print num_refused
        num_settled = (self.df.loc[self.df["simple_journal"] == "Settled"]).shape[0]
        print num_settled
        number_of_records = [num_chargeback, num_refused, num_settled]
        plt.bar(y_pos, number_of_records, align='center', alpha=0.4, color='red')
        plt.xticks(y_pos, objects)
        plt.ylabel('Number of Transactions', fontsize=20)
        #plt.title('Balance of the Data')
        plt.show()


    @staticmethod
    def normalize_all_columns(x):
        min_max_scaler = preprocessing.MinMaxScaler()
        x_scaled = min_max_scaler.fit_transform(x)
        return x_scaled

    @staticmethod
    # The minority class gets oversampled to balance with the majority class
    # Output format: X_resampled, y_resampled
    def resample_smote(X, y):
        sm = SMOTE()
        return sm.fit_sample(X, y)

    @staticmethod
    def string_to_timestamp(date_string):  # convert time string to float value
        time_stamp = time.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        return time.mktime(time_stamp)

    @staticmethod
    def get_percentage_of_frauds(trans_dict, chargebacks_dict):
        normalized_fpc = {}
        for key in trans_dict:
            if key in chargebacks_dict:
                normalized_fpc[key] = chargebacks_dict[key] / trans_dict[key]
        return normalized_fpc

    @staticmethod
    def plot_dictionary_sorted(D, figure_title, time_flag):
        if time_flag:
            sorted_D =  sorted(D.items(), key = operator.itemgetter(0))
        else:
            sorted_D = sorted(D.items(), key = operator.itemgetter(1))
        values = [x[1] for x in sorted_D]
        keys = [x[0] for x in sorted_D]
        plt.bar(range(len(sorted_D)), values, align='center',alpha=0.4, color = 'red')
        plt.xticks(range(len(sorted_D)), keys)
        #plt.xlabel('xlabel', fontsize=18)
        plt.ylabel('Number of Transactions', fontsize=20)
        #plt.title(figure_title)
        plt.show()

    @staticmethod
    def get_plots():
        # barplot with number of settled, chargebacks and refused transactions
        #trans_obj = Fraud()
        trans_obj.plot_data_balance()

        # get transactions per country (dictionary)
        trans_per_country = trans_obj.total_per_country()
        # print("Number of countries in the dataset: %d" % len(trans_per_country))

        # plot normalized fraud per countries
        # get fraud transactions per country (dictionary)

        #create chargeback object
        chargebacks_obj = Fraud()
        chargebacks_obj.df = chargebacks_obj.filter_records("Chargeback")

        fraud_per_country = chargebacks_obj.total_per_country()
        print("Number of countries with frauds in the dataset: %d" % len(fraud_per_country))
        normalized_fpc = Fraud.get_percentage_of_frauds(trans_per_country, fraud_per_country)
        Fraud.plot_dictionary_sorted(normalized_fpc, "Normalized number of Frauds per country", False)

        # plot normalized cardType
        # get transactions per card type (dictionary)
        trans_per_card_type = trans_obj.total_per_cardtype()
        # get fraud transactions per card type (dictionary)
        fraud_per_cardtype = chargebacks_obj.total_per_cardtype()
        normalized_cardtype = Fraud.get_percentage_of_frauds(trans_per_card_type, fraud_per_cardtype)
        Fraud.plot_dictionary_sorted(normalized_cardtype, "Normalized  number of frauds per cardtype", False)

        # plot normalized day month
        # get transactions per day (dictionary)
        trans_per_day_week = trans_obj.total_per_day_week()
        # get fraud transactions per card type (dictionary)
        fraud_per_day_week = chargebacks_obj.total_per_day_week()
        normalized_day_week = Fraud.get_percentage_of_frauds(trans_per_day_week, fraud_per_day_week)
        Fraud.plot_dictionary_sorted(normalized_day_week, "Normalized  number of frauds per day-week", True)

        # plot normalized day month
        # get transactions per month (dictionary)
        trans_per_day_month = trans_obj.total_per_day_month()
        # get fraud transactions per card type (dictionary)
        fraud_per_day_month = chargebacks_obj.total_per_day_month()
        normalized_day_month = Fraud.get_percentage_of_frauds(trans_per_day_month, fraud_per_day_month)
        Fraud.plot_dictionary_sorted(normalized_day_month, "Normalized  number of frauds per day-month", True)

        # plot normalized hour
        # get transactions per hour (dictionary)
        trans_per_hour = trans_obj.total_per_hour()
        # get fraud transactions per card type (dictionary)
        fraud_per_hour = chargebacks_obj.total_per_hour()
        normalized_hour = Fraud.get_percentage_of_frauds(trans_per_hour, fraud_per_hour)
        Fraud.plot_dictionary_sorted(normalized_hour, "Normalized  number of frauds per hour", True)


        # boxplots for settled and fraud amounts
        # get settled transactions
        settled_obj = Fraud()
        settled_obj.df = settled_obj.filter_records("Settled")

        fig, (ax1, ax2) = plt.subplots(1, 2, sharex=False, sharey=True)
        axes = settled_obj.df.boxplot(column="amount", ax=ax1, sym='', showfliers=True)
        ax1.margins(y=0.05)
        ax1.set_title("settled")

        box_chargeback = chargebacks_obj.df.boxplot(column="amount", ax=ax2, sym='', showfliers=True)
        ax2.margins(y=0.05)
        ax2.set_title("Chargeback")
        plt.show()

    ##############
    # CLASSIFIERS#
    ##############

    @staticmethod
    def knn(features_train, labels_train, variables):
        k = variables["k"]
        knn_classifier = KNeighborsClassifier(n_neighbors=k)
        knn_classifier.fit(features_train, labels_train)
        return knn_classifier

    @staticmethod
    def lda(features_train, labels_train, variables):
        lda_classifier = LinearDiscriminantAnalysis()
        lda_classifier.fit(features_train, labels_train)
        return lda_classifier


    @staticmethod
    def decision_tree(features_train, labels_train, variables):
        dt_classifier = tree.DecisionTreeClassifier()
        dt_classifier.fit(features_train, labels_train)
        return dt_classifier

    @staticmethod
    def random_forest(features_train, labels_train, variables):
        n = variables["n"]
        rf_classifier = RandomForestClassifier(n_jobs=n)
        rf_classifier.fit(features_train, labels_train)
        return rf_classifier

    @staticmethod
    def naive_bayes(features_train, labels_train, variables):
        nb = GaussianNB()
        nb.fit(features_train, labels_train)
        return nb

    @staticmethod
    def gradient_boost(features_train, labels_train, variables):
        params = {'n_estimators': variables["n_estimators"], 'max_depth': variables["max_depth"],
                  'min_samples_split': variables["min_samples_split"],
                  'learning_rate': variables["learning_rate"], 'loss': variables["loss"]}
        gb_classifier = GradientBoostingClassifier(**params)
        gb_classifier.fit(features_train, labels_train)
        return gb_classifier

    @staticmethod
    def majority_voting(features_train, labels_train, variables):
        classifiers_list = []
        for classifier_name in variables:
            model = variables[classifier_name]
            classifiers_list.append((classifier_name, model))
        mv_classifier = VotingClassifier(estimators = classifiers_list, voting='soft')
        mv_classifier = mv_classifier.fit(features_train, labels_train)
        return mv_classifier


    @staticmethod
    def get_classifier(name_classifier, features_train, labels_train, variables):
        classifiers = {"knn": Fraud.knn, "rf": Fraud.random_forest, "gb": Fraud.gradient_boost,
                       "nb": Fraud.naive_bayes, "lda": Fraud.lda, "mv": Fraud.majority_voting,
                       "dt": Fraud.decision_tree}
        return classifiers[name_classifier](features_train, labels_train, variables)

    @staticmethod
    def write_to_file(classifier_name, variables, results, k_fold, use_smote):
        result = "Variables: %s, k_fold: %s, use_smote: %s\nTP: %s\nFP: %s\nFN: %s\nTN: %s\nAccuracy: %s\nPrecision: %s\nRecall: %s\nAUC: %s\nF1: %s\n\n" % (
            str(variables), k_fold, str(use_smote), results["TP"], results["FP"], results["FN"], results["TN"],
            results["accuracy"],results["precision"],results["recall"], results["auc"], results["f1"]
        )
        with open(os.path.join("..", "results", classifier_name), "a") as myfile:
            myfile.write(result)
        myfile.close()

    @staticmethod
    def plot_roc(classifier_name, real_labels, probability_labels):
        false_positive_rate, true_positive_rate, _ = roc_curve(real_labels, probability_labels, pos_label=1)
        plt.figure()
        lw = 2
        plt.plot(false_positive_rate, true_positive_rate, color='darkorange',
                 lw=lw, label='ROC curve (area = %0.2f)' % auc(false_positive_rate, true_positive_rate))
        plt.plot([0, 1], [0, 1], color='navy', lw=lw, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver operating characteristic for %s' % classifier_name)
        plt.legend(loc="lower right")
        plt.show()

    @staticmethod
    def get_evaluation_metrics(real_labels, predicted_labels, probability_labels):
        print("Calculating evaluation metrics.")
        TP = 0
        FP = 0
        FN = 0
        TN = 0
        accuracy = accuracy_score(real_labels, predicted_labels)
        f1 = f1_score(real_labels, predicted_labels)
        precision = average_precision_score(real_labels, predicted_labels)
        recall = recall_score(real_labels, predicted_labels)
        auc = roc_auc_score(real_labels, probability_labels)

        for i in xrange(len(predicted_labels)):
            if real_labels[i] == 1 and predicted_labels[i] == 1:
                TP += 1
            if real_labels[i] == 0 and predicted_labels[i] == 1:
                FP += 1
            if real_labels[i] == 1 and predicted_labels[i] == 0:
                FN += 1
            if real_labels[i] == 0 and predicted_labels[i] == 0:
                TN += 1

        resulting_metrics = {"TP": TP, "FP": FP, "FN": FN, "TN": TN, "accuracy": accuracy, "f1": f1,
                             "precision":precision, "recall": recall, "auc": auc}
        print("Result:%s" % str(resulting_metrics))
        print("\tFinished!")
        return resulting_metrics

    @staticmethod
    def evaluate(feature_vector, labels, classifier_name, variables, use_smote):
        n_splits = 10

        # Print the distribution of the lables
        unique, counts = np.unique(labels, return_counts=True)
        print("Total label distribution", dict(zip(unique, counts)))

        convert_zero_one = lambda x: map(lambda y: 0 if y == "Settled" else 1, x)
        labels = np.array(convert_zero_one(labels))
        k_fold = StratifiedKFold(n_splits=n_splits)
        real_labels = []
        predicted_labels = []
        probability_labels = []
        print("Applying %s-fold crossvalidation with %s predictor, variables %s and smote=%s" % (n_splits, classifier_name,str(variables), str(use_smote)))
        for train, test in k_fold.split(feature_vector,labels):
            if use_smote:
                features_train, labels_train = Fraud.resample_smote(feature_vector[train], labels[train])
            else:
                features_train, labels_train = feature_vector[train], labels[train]
            features_test, labels_test = feature_vector[test], labels[test]

            # Print distribution of the labels of the current split
            unique, counts = np.unique(labels_test, return_counts=True)
            print("Current fold distribution", dict(zip(unique, counts)))

            # Build classifier using training set
            classifier = Fraud.get_classifier(classifier_name, features_train, labels_train, variables)


            # Save the labels
            real_labels.extend(labels_test)
            predicted_labels.extend(classifier.predict(features_test))
            probability_labels.extend(classifier.predict_proba(features_test))

        print("\tFinished")

        # Get the evaluation metrics
        probability_labels = np.array(probability_labels)[:, 1]
        resulting_metrics = Fraud.get_evaluation_metrics(real_labels, predicted_labels, probability_labels)

        print("Plot the ROC curve")
        Fraud.plot_roc(classifier_name, real_labels, probability_labels)
        print("\tFinished")

        print("Writing to file")
        Fraud.write_to_file(classifier_name, variables, resulting_metrics, n_splits, use_smote)
        print("\tFinished!")

        return resulting_metrics

    @staticmethod
    def reduce_dimensionality(feature_vector, labels, method):
        print("\tUsing %s" % method)
        if method == "pca":
            pca = decomposition.PCA(n_components=100)
            resulting_features = pca.fit_transform(feature_vector)
        elif method == "lda":
            lda = LinearDiscriminantAnalysis(n_components=50)
            resulting_features = lda.fit_transform(feature_vector, labels)
        return resulting_features


   # Run classifiers with different parameters
    @staticmethod
    def evaluate_knn(feature_vector, labels, smote):
        for i in range(4, 6):
            Fraud.evaluate(feature_vector, labels, "knn", {"k": i}, use_smote=smote)
    @staticmethod
    def evaluate_rf(feature_vector, labels, smote):
        for i in range(10, 20, 2):
            Fraud.evaluate(feature_vector, labels, "rf", {"n":i}, use_smote=smote)

    @staticmethod
    def hot_encoder(features_df, columns):
        le = preprocessing.LabelEncoder()
        for col_names in columns:
            features_df[col_names] = pd.Series(le.fit_transform(features_df[col_names].values))

    # LET THE MAGIC BEGIN
    def run(self):

        # remove REFUSED transactions
        self.df = self.df[self.df.simple_journal != "Refused"]

        hot_encoding = False
        list_with_categorical_columns = ["txvariantcode", "shopperinteraction", "issuercountrycode", "currencycode",
                                         "shoppercountrycode", "accountcode", "card_id", "ip_id", "mail_id"]

        if hot_encoding:
            filtered_df = self.get_selected_features(selected_features)
            filtered_df = filtered_df.dropna(axis=0, how='any')
            print("Hot encoding")
            Fraud.hot_encoder(filtered_df, list_with_categorical_columns)
            filtered_df = filtered_df.dropna(axis=0, how='any')
            features_without_labels = list(filtered_df)
            features_without_labels.remove(label)
            resulting_feature_vector, labels_list = Fraud.get_records_and_labels(filtered_df, features_without_labels)
            print len(resulting_feature_vector[3])

        else:
            print("Creating dummy variables.")
            filtered_df = self.get_selected_features(selected_dummy_features)
            filtered_df = filtered_df.dropna(axis=0, how='any')
            filtered_df = pd.get_dummies(filtered_df,
                                   columns=["txvariantcode", "shoppercountrycode", "shopperinteraction","issuercountrycode", "currencycode", "accountcode"])
            print("Reducing dimensionality.")
            features_without_labels = list(filtered_df)
            features_without_labels.remove(label)
            features_list, labels_list = Fraud.get_records_and_labels(filtered_df, features_without_labels)
            resulting_feature_vector = Fraud.reduce_dimensionality(features_list, labels_list, "lda")
            #uncomment line if you don't want dimensionality reduction
            #resulting_feature_vector = features_list
            print("\tFinished!!")


        print("Building classifier and apply (or not) SMOTE")
        smote = False

        print("Build KNN classifier")
        #Fraud.evaluate(resulting_feature_vector, labels_list, "knn", {"k":4}, use_smote=smote)

        print("Build Random Forest classifier")
        #Fraud.evaluate(resulting_feature_vector, labels_list, "rf", {"n":90}, use_smote=smote)

        print("Build Decision Tree classifier")
        #Fraud.evaluate(resulting_feature_vector, labels_list, "dt", {}, use_smote=smote)

        print("Build Naive Bayes classifier")
        #Fraud.evaluate(resulting_feature_vector, labels_list, "nb", {}, use_smote=smote)

        print("Build lda classifier")
        #Fraud.evaluate(resulting_feature_vector, labels_list, "lda", {}, use_smote=smote)

        print("Build gradient boost classifier")
        # set parameters
        estimators = 100
        loss = "exponential"
        learning = 0.1
        params = {'n_estimators': estimators, 'max_depth': 3, 'min_samples_split': 2,
                    'learning_rate': learning, 'loss': loss}
        Fraud.evaluate(resulting_feature_vector, labels_list, "gb", params, use_smote=False)

        print("Build majority voting classifier")
        #mv_params = {"knn":KNeighborsClassifier(n_neighbors=4), "nb": GaussianNB(), "lda": LinearDiscriminantAnalysis(),
        #                "rf": RandomForestClassifier(n_jobs=5), "gb": GradientBoostingClassifier(**params),
        #                "dt": tree.DecisionTreeClassifier()}
        #Fraud.evaluate(resulting_feature_vector, labels_list, "mv", mv_params, use_smote=False)
        print("Finished!!")


# Initialization of dataframe object (transactions)
trans_obj = Fraud()

# RUN CLASSIFIERS
trans_obj.run()

# RUN VISUALIZATIONS
#Fraud.get_plots()

