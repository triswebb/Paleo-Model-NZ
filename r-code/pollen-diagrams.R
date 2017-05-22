require(rioja)
data(aber)
depth <- aber$ages$Age
spec <- aber$spec
depth1 = c(1,2,3)
species = data.frame(a = c(1,2,3), b=c(3,6,2))

# basic silhouette plot
strat.plot(species, yvar = depth1, y.rev=TRUE, scale.percent=TRUE, ylabel="Depth (cm)",
           plot.poly=TRUE, col.poly="darkgreen", col.poly.line=1)
