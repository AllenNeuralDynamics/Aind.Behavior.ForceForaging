using Bonsai;
using System;
using System.ComponentModel;
using System.Linq;
using System.Reactive.Linq;
using Bonsai.Harp;
using System.Xml.Serialization;

[Combinator]
[Description("Applies a LoadCellsCalibration object to a sequence of load cell data values. The correction is applied in the form of: grams = (adc_value - baseline) * slope.")]
[WorkflowElementCategory(ElementCategory.Transform)]
public class ApplyLoadCellsCalibration
{
    [XmlIgnore]
    public LoadCellsCalibrations Calibration {get; set;}

    public IObservable<Timestamped<double[]>> Process(IObservable<Timestamped<short[]>> source)
    {
        return source.Select(value => {
            var data = value.Value.Select(v => (double) v).ToArray();
            if (Calibration == null) return Timestamped.Create(data, value.Seconds);

            foreach (var loadCell in Calibration)
            {
                data[loadCell.LoadCellIndex] = (data[loadCell.LoadCellIndex] - loadCell.Baseline) * loadCell.Slope;
            }
            return Timestamped.Create(data, value.Seconds);
        });
    }
}
