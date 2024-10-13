import os


class Configuration:
    def __init__(
        self,
        repositoryUrl: str,
        batchMonths: int,
        outputPath: str,
        sentiStrengthPath: str,
        maxDistance: int,
        pat: str,
        googleKey: str,
        startDate: str,
    ):
        self.repositoryUrl = repositoryUrl
        self.batchMonths = batchMonths
        self.outputPath = outputPath
        self.sentiStrengthPath = sentiStrengthPath
        self.maxDistance = maxDistance
        self.pat = pat
        self.googleKey = googleKey
        self.startDate = startDate

        # parse repo name into owner and project name
        split = self.repositoryUrl.split("/")
        self.repositoryOwner = split[3]
        self.repositoryName = split[4]

        # build repo path
        self.repositoryPath = os.path.join(self.outputPath, split[3], split[4])

        # build results path
        self.resultsPath = os.path.join(self.repositoryPath, "results")

        # build metrics path
        self.metricsPath = os.path.join(self.resultsPath, "metrics")
