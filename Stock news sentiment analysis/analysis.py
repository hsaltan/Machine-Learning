# Import libraries
from colorama import Fore, Back, Style
import pandas as pd
import matplotlib.pyplot as plt
import itertools
from scipy.stats import pearsonr
import statsmodels.api as sm
import numpy as np
import warnings


warnings.filterwarnings("ignore")

# Define the region and boto3 clients
region = "eu-west-1"

# Prices and returns
dates = ["P_at_0d", "P_bef_15d", "P_bef_7d", "P_bef_3d", "P_aft_3d", "P_aft_7d", "P_aft_15d"]
returns = ["R_at_0d", "R_bef_15d", "R_bef_7d", "R_bef_3d", "R_aft_3d", "R_aft_7d", "R_aft_15d"]
lower_returns = [r.lower() for r in returns]

# Plot the data
custom_ylim = (-20, 20)
def get_axis_limits(ax, scale_x=.80, scale_y=.90):
    return ax.get_xlim()[1]*scale_x, custom_ylim[1]*scale_y

def plot_data(positive_list, negative_list, title, plotName):

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=[15, 5], dpi=120, facecolor='#C1E0E3')
    fig.subplots_adjust(top=0.85)
    fig.suptitle(title, fontsize=18)

    colors = ['C0', 'C1', 'C2', 'C3', 'C4']
    labels = ["all", "lowest", "low", "high", "highest"]
    x_values = lower_returns[1:]

    for chart in range(5):

        # Find the number of news articles by group and in total
        noOfPositiveArticles = len(positive_list[0])
        noOfNegativeArticles = len(negative_list[0])
        noOfPositiveArticlesByGroup = len(positive_list[chart])
        noOfNegativeArticlesByGroup = len(negative_list[chart])
        
        # Find the mean of each column in the dataframe
        mean_positive_df = positive_list[chart].mean()
        mean_negative_df = negative_list[chart].mean()

        # Plot
        ax1.plot(mean_positive_df[x_values], colors[chart], label=labels[chart] + ": " + str(noOfPositiveArticlesByGroup) + " news")
        ax2.plot(mean_negative_df[x_values], colors[chart], label=labels[chart] + ": " + str(noOfNegativeArticlesByGroup) + " news")

    ax1.set_title('Stock Return Change for Positive Polarity', fontsize=14)
    ax2.set_title('Stock Return Change for Negative Polarity', fontsize=14)

    ax1.set_ylabel('Stock Returns (%)', fontsize = 12)
    ax1.set_xlabel('Time', fontsize = 12)
    ax2.set_ylabel('Stock Returns (%)', fontsize = 12)
    ax2.set_xlabel('Time', fontsize = 12)

    ax1.grid(axis="y", alpha = 0.5)
    ax2.grid(axis="y", alpha = 0.5)

    color = '#ffa31a'
    ax1.axhline(y=0, color=color, linestyle='-', alpha=0.5)
    ax1.axvline(x="r_bef_3d", color=color, linestyle='-', alpha=0.5)
    ax1.axvline(x="r_aft_3d", color=color, linestyle='-', alpha=0.5)
    ax2.axhline(y=0, color=color, linestyle='-', alpha=0.5)
    ax2.axvline(x="r_bef_3d", color=color, linestyle='-', alpha=0.5)
    ax2.axvline(x="r_aft_3d", color=color, linestyle='-', alpha=0.5)

    # Add annotation
    ax1Annotation = str(noOfPositiveArticles) + " news"
    ax1.annotate(ax1Annotation, xy=get_axis_limits(ax1), horizontalalignment='left', verticalalignment='top', transform=ax1.transAxes, fontsize=10, bbox=dict(facecolor=color, alpha=0.5))
    ax2Annotation = str(noOfNegativeArticles) + " news"
    ax2.annotate(ax2Annotation, xy=get_axis_limits(ax2), horizontalalignment='left', verticalalignment='top', transform=ax2.transAxes, fontsize=10, bbox=dict(facecolor=color, alpha=0.5))

    plt.setp((ax1, ax2), ylim=custom_ylim)

    ax1.legend(loc='lower left', fontsize='x-small')
    ax2.legend(loc='lower left', fontsize='x-small')

    # Save the plot
    plt.savefig(plotName, orientation='portrait', format='png')
    plt.show()

# Calculate Pearson correlations between before and after returns for each score calculation
def calculate_correlation(positive_dfs, negative_dfs, description):

    # Data containers
    labels = ["All         ", "Lowest group", "Low group", "High group", "Highest group"]
    correlation_keys = {}
    positive_polarity_correlations = {}
    negative_polarity_correlations = {}
    significant_positive_polarity_correlations = {}
    significant_negative_polarity_correlations = {}
    dyads = []

    # Significant test threshold value
    alpha = 0.05

    # Combine each element of the before-return list with each element of the after-return list
    before_returns = lower_returns[1:4]
    after_returns = lower_returns[4:7]
    for pair in itertools.product(before_returns, after_returns):
        dyads.append(pair)

    # Calculate the correlations between tuple elements for positive polarity dataframes
    l = 0
    print('\n')
    print(f"{Fore.MAGENTA}The highest significant {Fore.RED}positive polarity{Style.RESET_ALL} {Fore.MAGENTA}{description}: {Style.RESET_ALL}")
    for positive_df in positive_dfs:
        for dyad in dyads:
            X = positive_df[dyad[0]]
            Y = positive_df[dyad[1]]
            if len(X) > 2 and len(Y) > 2:
                corr = pearsonr(X, Y)
                positive_polarity_correlations[dyad] = (round(corr[0], 3), round(corr[1], 5))
            else:
                continue

        # Determine the correlations which are significant for positive polarity dataframes
        for key, value in positive_polarity_correlations.items():
            if value[1] < alpha/2:
                significant_positive_polarity_correlations[key] = abs(value[0])
            else:
                continue

        # Find the highest significant correlation time periods for positive polarity dataframes
        if significant_positive_polarity_correlations:
            positivePolarityCorrMaxKey = max(significant_positive_polarity_correlations, key=significant_positive_polarity_correlations.get)
            positivePolarityCorrMaxValue = positive_polarity_correlations[positivePolarityCorrMaxKey]

        # Find the max key, value of the 'All' and save it in a dictionary
        if l == 0:
            correlation_keys['positive_polarity'] = (positivePolarityCorrMaxKey, positivePolarityCorrMaxValue)

        print('\n')
        print(f"{Fore.CYAN}{l+1}.\t{Style.RESET_ALL}{Fore.CYAN}{labels[l]}\t{Style.RESET_ALL}{Fore.LIGHTBLUE_EX}{positivePolarityCorrMaxKey}:{Style.RESET_ALL} {Fore.GREEN}{positivePolarityCorrMaxValue}{Style.RESET_ALL}")
        l += 1
    print('\n')

    # Calculate the correlations between tuple elements for negative polarity dataframes
    l = 0
    print('\n')
    print(f"{Fore.MAGENTA}The highest significant {Fore.RED}negative polarity{Style.RESET_ALL} {Fore.MAGENTA}{description}: {Style.RESET_ALL}")
    for negative_df in negative_dfs:
        for dyad in dyads:
            X = negative_df[dyad[0]]
            Y = negative_df[dyad[1]]
            if len(X) > 2 and len(Y) > 2:
                corr = pearsonr(X, Y)
                negative_polarity_correlations[dyad] = (round(corr[0], 3), round(corr[1], 5))
            else:
                continue

        # Determine the correlations which are significant for negative polarity dataframes
        for key, value in negative_polarity_correlations.items():
            if value[1] < alpha/2:
                significant_negative_polarity_correlations[key] = abs(value[0])
            else:
                continue

        # Find the highest significant correlation time periods for negative polarity dataframes
        if significant_negative_polarity_correlations:
            negativePolarityCorrMaxKey = max(significant_negative_polarity_correlations, key=significant_negative_polarity_correlations.get)
            negativePolarityCorrMaxValue = negative_polarity_correlations[negativePolarityCorrMaxKey]

        # Find the max key, value of the 'All' and save it in a dictionary
        if l == 0:
            correlation_keys['negative_polarity'] = (negativePolarityCorrMaxKey, negativePolarityCorrMaxValue)

        print('\n')
        print(f"{Fore.CYAN}{l+1}.\t{Style.RESET_ALL}{Fore.CYAN}{labels[l]}\t{Style.RESET_ALL}{Fore.LIGHTBLUE_EX}{negativePolarityCorrMaxKey}:{Style.RESET_ALL} {Fore.GREEN}{negativePolarityCorrMaxValue}{Style.RESET_ALL}")
        l += 1
    print('\n')
    return correlation_keys

# Do regression analysis and plot the results
def perform_linear_regression(name, key, polarity_tuple, df):

    # Plot the graph of returns of the two periods that have the highest significant correlation.
    x_label = polarity_tuple[0]
    y_label = polarity_tuple[1]
    X = df[x_label]
    y = df[y_label]
    _, ax = plt.subplots(figsize=[12, 6], dpi=120, facecolor='#C1E0E3')
    ax.set_title(name, fontsize=16)
    ax.set_xlabel(x_label + ' (%)', fontsize = 11)
    ax.set_ylabel(y_label + ' (%)', fontsize = 11)
    ax.grid(axis="both", alpha = 0.5)
    ax.grid(axis="both", alpha = 0.5)
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    plt.scatter(X, y)
    plt.savefig(x_label + "_vs_" + y_label + "_for_" + key + ".png", orientation='portrait', format='png')
    plt.show()
    print('\n')

    # Perform linear regression
    X = sm.add_constant(X)
    model = sm.OLS(y, X)  
    results = model.fit()
    residuals = results.resid
    print(f"{Fore.MAGENTA}Results Summary for {name}{Style.RESET_ALL}")
    print('\n')
    print(f"{Fore.GREEN}")
    print(results.summary())
    {Style.RESET_ALL}
    print('\n')

    # Evaluation metrics
    print(f"{Fore.MAGENTA}R2: {Style.RESET_ALL}{Fore.GREEN}{results.rsquared}{Style.RESET_ALL}")
    print('\n')
    print(f"{Fore.MAGENTA}Number of observations: {Style.RESET_ALL}{Fore.GREEN}{results.nobs}{Style.RESET_ALL}")
    print('\n')
    print(f"{Fore.MAGENTA}Standard errors:\n{Style.RESET_ALL}{Fore.GREEN}{results.bse}{Style.RESET_ALL}")
    print('\n')
    print(f"{Fore.MAGENTA}F: {Style.RESET_ALL}{Fore.GREEN}{results.mse_model/results.mse_resid}{Style.RESET_ALL}")
    print('\n')

    residuals.plot(kind='hist', bins=30)
    plt.title('Histogram for Residuals for ' + key.replace("_", " ").title())
    plt.savefig("histogram_for_residuals_for_" + key + ".png", orientation='portrait', format='png')
    plt.show()

    return results

# Do sensitivity analysis to assess risk and plot the results
def assess_risk(correlation_keys, dfs):

    for key, value in correlation_keys.items():
        polarity_tuple = value[0]
        df = dfs[key]
        name = key.replace("_", " ").title()
        results = perform_linear_regression(name, key, polarity_tuple, df)

        # Find the linear regression parameters
        constant = results.params[0]
        beta = results.params[1]
        constantSE = results.bse[0]
        betaSE = results.bse[1]

        # Calculate the minimum and maximum y values given the model
        minConstantValue = constant - 2 * constantSE
        maxConstantValue = constant + 2 * constantSE
        minBetaValue = beta - 2 * betaSE
        maxBetaValue = beta + 2 * betaSE

        # Plot the min and max y values for different levels of x value
        test_x_values = range(-10, 11, 2)
        min_y_values = [z * minBetaValue + minConstantValue for z in test_x_values]
        max_y_values = [z * maxBetaValue + maxConstantValue for z in test_x_values]

        # Find the min and max tuples that are in the same direction
        zipped_list = list(zip(min_y_values, max_y_values))
        diff_sign_list = [(x[0], x[1], np.sign(x[0])) for x in zipped_list if (np.sign(x[0]) * np.sign(x[1])) >= 0]

        # Find the plot x and y locations of the same direction tuples
        y_locations = [max(abs(x[0]), abs(x[1])) * x[2] for x in diff_sign_list]
        x_locations = [max_y_values.index(x) if x in max_y_values else min_y_values.index(x) for x in y_locations]
        x_y_zipped_locations = list(zip(x_locations, y_locations))

        # Find the tuple that is the least in sum value
        sum_y_values = [abs(x[0]) + abs(x[1]) for x in list(zip(min_y_values, max_y_values))]
        minSumValue = min(sum_y_values)

        # Find the plot x location of the least sum value tuple
        index = sum_y_values.index(minSumValue)

        # Create a dataframe of possible minimum and maximum return values following the news article date against the realized returns before it
        df = pd.DataFrame({'before_returns': test_x_values, 'min_after_returns' : min_y_values, 'max_after_returns': max_y_values})
        df = df.round(2)

        # Plot the dataframe
        ax = df.plot(x="before_returns", y=["min_after_returns", "max_after_returns"], kind="bar", figsize=[15, 8], fontsize=9, legend=False)
        ax.grid(axis="y", alpha = 0.5)

        # Draw a vertical line accross the x axis at the the least sum value tuple
        ax.axvline(x=index, color='g', linestyle='-', alpha=0.5)

        # Mark the same direction tuples of min and max return values with "*"
        n = 1
        for loc in x_y_zipped_locations:
            ax.text(loc[0]-0.15, loc[1]-0.15, n, color = '#6F0B14', fontweight = 'bold', fontsize = 10)
            n += 1

        # Add x and y labels and title
        plt.xlabel("before_returns (%)", fontsize=11)
        plt.ylabel("after_returns (%)", fontsize=11)
        plt.gcf().suptitle("{} Possible After Return Values for Different Levels of Before Return Values".format(name), fontsize=16)

        # Save the plot
        plt.savefig("min_and_max_after_returns_for_" + key + ".png", orientation='portrait', format='png')
        plt.show()
        print('\n')
