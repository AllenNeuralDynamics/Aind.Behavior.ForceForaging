using Bonsai;
using System;
using System.ComponentModel;
using System.Collections.Generic;
using System.Linq;
using System.Reactive.Linq;
using System.Collections.ObjectModel;

[Combinator]
[Description("Parses a sequence of Tuple<Offset, Baseline, LoadCellIndex> into a LoadCellsCalibrations object.")]
[WorkflowElementCategory(ElementCategory.Transform)]
public class ParseLoadCellsCalibration
{
    public IObservable<LoadCellsCalibrations> Process(IObservable<IEnumerable<Tuple<int, int, int>>> source)
    {
        return source.Select(value => {
            var calibrations = new LoadCellsCalibrations();
            foreach (var calibration in value)
            {
                calibrations.Add(new LoadCellCalibration
                {
                    Offset = calibration.Item1,
                    Baseline = calibration.Item2,
                    LoadCellIndex = calibration.Item3
                });
            }
            return calibrations;
        });
    }
}


public class LoadCellCalibration{
    public int Offset { get; set; }
    public int Baseline { get; set; }
    public int LoadCellIndex { get; set; }
}

public class LoadCellsCalibrations : KeyedCollection<int, LoadCellCalibration>
{
    protected override int GetKeyForItem(LoadCellCalibration item)
    {
        return item.LoadCellIndex;
    }
}