from __future__ import division
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
import operator


data_path = '../datasets/data_for_student_case.csv'
columns = ["txid", "bookingdate", "issuercountrycode", "txvariantcode", "card_issuer_identifier",
           "amount", "currencycode", "shoppercountrycode", "shopperinteraction", "simple_journal",
           "cardverificationcodesupplied", "cvcresponsecode", "creationdate", "accountcode", "mail_id",
           "ip_id", "card_id"]

class Fraud:
    def __init__(self):
        self.load_data()

    def load_data(self):
        # Read from csv
        self.df = pd.read_csv(data_path, skip_blank_lines=True)

        # Rename a column
        self.df.rename(columns={'bin': 'card_issuer_identifier'}, inplace=True)
        # Delete rows with null values for card_issuer_identifier
        self.df = self.df[pd.notnull(self.df.card_issuer_identifier)]
        #self.df = self.df[self.df.simple_journal != "Refused"]

        # Change data types of some columns
        self.df["bookingdate"].apply(self.string_to_timestamp)
        self.df["card_issuer_identifier"].apply(float)
        self.df["amount"].apply(lambda x: float(x)/100)

    # Output format: {"US": 112, ...}
    def total_per_country(self):
        result = self.df["issuercountrycode"].value_counts().to_dict()
        #result.to_csv(path=path,index_label=["issuercountrycode","transaction_count"],index=True)
        return result

    # Output: dictionary
    def total_per_cardtype(self):
        result = self.df["txvariantcode"].value_counts().to_dict()
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
        num_refused = self.df.loc[self.df["simple_journal"] == "Refused"].shape[0]
        num_settled = (self.df.loc[self.df["simple_journal"] == "Settled"]).shape[0]
        number_of_records = [num_chargeback, num_refused, num_settled]
        plt.bar(y_pos, number_of_records, align='center', alpha=0.4, color='red')
        plt.xticks(y_pos, objects)
        plt.ylabel('Number of Transactions`')
        plt.title('Balance of the Data')
        plt.show()

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
    def plot_dictionary_sorted(D, figure_title):
        sorted_D = sorted(D.items(), key = operator.itemgetter(1))
        values = [x[1] for x in sorted_D]
        keys = [x[0] for x in sorted_D]
        plt.bar(range(len(sorted_D)), values, align='center',alpha=0.4, color = 'red')
        plt.xticks(range(len(sorted_D)), keys)
        plt.title(figure_title)
        plt.show()

    @staticmethod
    def get_plots():
        # barplot with number of settled, chargebacks and refused transactions
        trans_obj = Fraud()
        trans_obj.plot_data_balance()
        # get transactions per country (dictionary)
        trans_per_country = trans_obj.total_per_country()
        # print("Number of countries in the dataset: %d" % len(trans_per_country))

        # plot normalized fraud per countries
        # get fraud transactions per country (dictionary)
        chargebacks_obj = Fraud()
        chargebacks_obj.df = chargebacks_obj.filter_records("Chargeback")
        fraud_per_country = chargebacks_obj.total_per_country()
        print("Number of countries with frauds in the dataset: %d" % len(fraud_per_country))
        normalized_fpc = Fraud.get_percentage_of_frauds(trans_per_country, fraud_per_country)
        Fraud.plot_dictionary_sorted(normalized_fpc, "Normalized number of Frauds per country")

        # plot normalized cardType
        # get transactions per card type (dictionary)
        trans_per_card_type = trans_obj.total_per_cardtype()
        # get fraud transactions per card type (dictionary)
        fraud_per_cardtype = chargebacks_obj.total_per_cardtype()
        normalized_cardtype = Fraud.get_percentage_of_frauds(trans_per_card_type, fraud_per_cardtype)
        Fraud.plot_dictionary_sorted(normalized_cardtype, "Normalized  number of frauds per cardtype")

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


# Initialization of dataframe object (transactions)
trans_obj = Fraud()
print(trans_obj.df.shape)


#filter the dataframe per simple_journal category
chargebacks_obj = Fraud()
chargebacks_obj.df = chargebacks_obj.filter_records("Chargeback")
settled_obj = Fraud()
settled_obj.df = settled_obj.filter_records("Settled")
#refused_obj = Fraud()
#refused_obj.df = refused_obj.filter_records("Refused")

print(trans_obj.df["amount"].max())
print(settled_obj.df["amount"].max())
print(chargebacks_obj.df["amount"].max())



#get plots
#Fraud.get_plots()


# NOTES
# simple_journal = {Settled, Chargeback} We have removed "Refused"

# print the different values of 'simple_journal'
#print(trans_obj.df["simple_journal"].unique())