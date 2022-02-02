
import pandas as pd
from matplotlib import pyplot as plt

###
# Plot fitness for different islands during evolution
###

num_players = 5

main_dir = "final_results/" + str(num_players) + "p/"

df_0 = pd.read_csv(main_dir + "log_0.csv")
df_1 = pd.read_csv(main_dir + "log_1.csv")
df_2 = pd.read_csv(main_dir + "log_2.csv")
df_3 = pd.read_csv(main_dir + "log_3.csv")

global_best = []
save_next = False
with open(main_dir + "log_main.txt", "r") as f:
    for line in f:
        for word in line.split():
            if save_next:
                global_best.append(-float(word.strip().strip(",")))
                save_next = False            
            if word == "score":
                save_next = True

plt.plot(range(1, len(df_0.iloc[:,2]) + 1), -df_0.iloc[:,2], '--')
plt.plot(range(1, len(df_1.iloc[:,2]) + 1), -df_1.iloc[:,2], '--')
plt.plot(range(1, len(df_2.iloc[:,2]) + 1), -df_2.iloc[:,2], '--')
plt.plot(range(1, len(df_3.iloc[:,2]) + 1), -df_3.iloc[:,2], '--')
plt.plot(range(10, 101, 10), global_best, '-o')
plt.xlabel("Generation")
plt.ylabel("Score")
plt.plot()
plt.legend(["island 0", "island 1", "island 2", "island 3", "global"])
plt.savefig(str(num_players) + "p.png")

