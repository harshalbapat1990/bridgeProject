from bda.domain import AnalyticalMultiModel


class PostProcessing:
    def __init__(self, multiModel: AnalyticalMultiModel, *args, **kwargs):
        self.multiModel = multiModel

    def run(self):
        step1 = CheckGirder(multiModel=self.multiModel)
        step1.run()

        step2 = CheckPiers(multiModel=self.multiModel)
        step2.run()
        