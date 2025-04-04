from neuralforecast.auto import AutoNBEATSx, AutoNHITS, AutoDeepNPTS, AutoMLP, AutoNBEATS, AutoNLinear, AutoTiDE, \
    AutoPatchTST, AutoAutoformer, AutoFEDformer, AutoInformer, AutoTFT, AutoVanillaTransformer

import plot_utility
import yfinance_service
from neuralforecast import NeuralForecast

if __name__ == "__main__":
    ticker = '^GSPC'

    close = yfinance_service.get_close_as_series(ticker, period='max', interval='1d')

    # input_size = 250
    horizon = 5

    nf = NeuralForecast(
        models = [
            # NBEATS(input_size=250, h=horizon),

            AutoNBEATSx(h=horizon),
            AutoNHITS(h=horizon),
            AutoDeepNPTS(h=horizon),
            AutoMLP(h=horizon),
            AutoNBEATS(h=horizon),
            AutoNLinear(h=horizon),
            AutoTiDE(h=horizon),

            # AutoAutoformer(h=horizon),
            # AutoFEDformer(h=horizon),
            AutoInformer(h=horizon),
            AutoPatchTST(h=horizon),
            AutoTFT(h=horizon),
            AutoVanillaTransformer(h=horizon),
        ],
        freq = 'D'
    )

    nf.fit(df=close)

    predictions = nf.predict()

    print(predictions)

    plot_utility.plot_prediction(
        ticker,
        ticker,
        close.tail(2 * horizon),
        predictions,
    )
