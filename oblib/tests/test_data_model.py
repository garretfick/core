# Copyright 2018 Jonathan Xia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from data_model import Entrypoint, Context
from datetime import datetime
from taxonomy import getTaxonomy

class TestDataModelEntrypoint(unittest.TestCase):

    def setUp(self):
        self.taxonomy = getTaxonomy()

    def tearDown(self):
        pass

    def _check_arrays_equivalent(self, array1, array2):
        # An ugly hack to make the tests work in both python2
        # and python3:
        if hasattr( self, 'assertCountEqual'):
            self.assertCountEqual(array1, array2)
        else:
            self.assertItemsEqual(array1, array2)

        # assertCountEqual is the new name for what was previously
        # assertItemsEqual. assertItemsEqual is unsupported in Python 3
        # but assertCountEqual is unsupported in Python 2.


    def test_instantiate_empty_entrypoint(self):
        doc = Entrypoint("CutSheet", self.taxonomy)

        # The newly initialized CutSheet should have a correct list of
        # allowable concepts as defined by the taxonomy for CutSheets:
        concepts = doc.allowedConcepts()
        # TypeOfDevice is allowed in CutSheets:
        self.assertIn('solar:TypeOfDevice', concepts)
        # AppraisalCounterparties is not allowed in CutSheets:
        self.assertNotIn('solar:AppraisalCounterparties', concepts)

        # The newly initialized CutSheet should have a correct list of tables
        # and each table should have a correct list of axes, as defined by
        # the taxonomy for CutSheets:
        tables = doc.getTableNames()
        self._check_arrays_equivalent(tables,
                                      ["solar:InverterPowerLevelTable",
                                       "solar:CutSheetDetailsTable"])
        self._check_arrays_equivalent(
            doc.getTable("solar:InverterPowerLevelTable").axes(),
                         ["solar:ProductIdentifierAxis",
                          "solar:InverterPowerLevelPercentAxis"])
        self._check_arrays_equivalent(
            doc.getTable("solar:CutSheetDetailsTable").axes(),
                         ["solar:ProductIdentifierAxis",
                          "solar:TestConditionAxis"])

    def test_get_table_for_concept(self):
        doc = Entrypoint("CutSheet", self.taxonomy)
        # The CutSheet instance should know that RevenueMeterFrequency
        # is a concept that belongs in the CutSheetDetailsTable
        table = doc.getTableForConcept("solar:RevenueMeterFrequency")
        self.assertEqual(table.name(), "solar:CutSheetDetailsTable")

        table = doc.getTableForConcept("solar:InverterEfficiencyAtVmaxPercent")
        self.assertEqual(table.name(), "solar:InverterPowerLevelTable")

        # but if we ask for something that is not a line item concept,
        # getTableForConcept should return None:
        table = doc.getTableForConcept("solar:CutSheetDetailsTable")
        self.assertIsNone(table)


    def test_can_write_concept(self):
        doc = Entrypoint("CutSheet", self.taxonomy)

        # Not every concept is writable. For instance, we shouldn't be able
        # to write a value for an Abstract concept, a LineItem group, an Axis,
        # a Domain, etc. even though those are part of this entrypoint.
        self.assertFalse( doc.canWriteConcept('solar:ProductIdentifierModuleAbstract'))
        self.assertTrue( doc.canWriteConcept('solar:TypeOfDevice'))
        self.assertFalse( doc.canWriteConcept('solar:CutSheetDetailsLineItems'))

        self.assertFalse( doc.canWriteConcept('solar:CutSheetDetailsTable'))
        self.assertFalse( doc.canWriteConcept('solar:TestConditionDomain'))

        self.assertFalse( doc.canWriteConcept('solar:ProductIdentifierAxis'))
        self.assertTrue( doc.canWriteConcept('solar:ProductIdentifier'))

    def test_sufficient_context_instant_vs_duration(self):
        doc = Entrypoint("CutSheet", self.taxonomy)

        # in order to set a concept value, sufficient context must be
        # provided. what is sufficient context varies by concept.
        # in general the context must provide the correct time information
        # (either duration or instant)

        # We shouldn't even be able to instantiate a context with no time info:
        with self.assertRaises(Exception):
            noTimeContext = Context(ProductIdentifierAxis = "placeholder",
                                    TestConditionAxis= "placeholder")

        # solar:DeviceCost has period_type instant
        # so it requires a context with an instant. A context without an instant
        # should be insufficient:
        instantContext = Context(ProductIdentifierAxis = "placeholder",
                                 TestConditionAxis = "placeholder",
                                 instant = datetime.now())
        durationContext = Context(ProductIdentifierAxis = "placeholder",
                           TestConditionAxis = "placeholder",
                           duration = "forever")

        self.assertTrue( doc.sufficientContext("solar:DeviceCost",
                                                instantContext))
        # A context with a duration instead of an instant should also be
        # rejected:
        with self.assertRaises(Exception):
            doc.sufficientContext("solar:DeviceCost", durationContext)

        # solar:ModuleNameplateCapacity has period_type duration.
        # A context with an instant instead of a duration should also be
        # rejected:
        with self.assertRaises(Exception):
            doc.sufficientContext("solar:ModuleNameplateCapacity", instantContext)
        self.assertTrue( doc.sufficientContext("solar:ModuleNameplateCapacity",
                                               durationContext))


    def test_sufficient_context_axes(self):
        doc = Entrypoint("CutSheet", self.taxonomy)

        # The context must also provide all of the axes needed to place the
        # fact within the right table.

        # DeviceCost is on the CutSheetDetailsTable so it needs a value
        # for ProductIdentifierAxis and TestConditionAxis.
        with self.assertRaises(Exception):
            doc.sufficientContext("solar:DeviceCost", {})

        context = Context(instant = datetime.now(),
                          ProductIdentifierAxis = "placeholder",
                          TestConditionAxis = "placeholder")
        self.assertTrue( doc.sufficientContext("solar:DeviceCost", context) )

        badContext = Context(instant = datetime.now(),
                             TestConditionAxis = "placeholder")
        with self.assertRaises(Exception):
            doc.sufficientContext("solar:DeviceCost", badContext)

        badContext = Context(instant = datetime.now(),
                             ProductIdentifierAxis = "placeholder")
        with self.assertRaises(Exception):
            doc.sufficientContext("solar:DeviceCost", badContext)


        # How do we know what are valid values for ProductIdentifierAxis and
        # TestConditionAxis?  (I think they are meant to be UUIDs.)

        # Note: TestConditionAxis is part of the following relationships:
        # solar:TestConditionAxis -> dimension-domain -> solar:TestConditionDomain
        # solar:TestConditionAxis -> dimension-default -> solar:TestConditionDomain
        # i wonder what that "dimension-default" means

        #'solar:InverterOutputRatedPowerAC' is on the 'solar:InverterPowerLevelTable' which requires axes: [u'solar:ProductIdentifierAxis', u'solar:InverterPowerLevelPercentAxis']. it's a duration.
        concept = 'solar:InverterOutputRatedPowerAC'
        context = Context(duration = "forever",
                          ProductIdentifierAxis = "placeholder",
                          InverterPowerLevelPercentAxis = "placeholder")
        self.assertTrue( doc.sufficientContext(concept, context))

        badContext = Context(instant = datetime.now(),
                             InverterPowerLevelPercentAxis = "placeholder")
        with self.assertRaises(Exception):
            doc.sufficientContext(concept, badContext)

        badContext = Context(instant = datetime.now(),
                             ProductIdentifierAxis = "placeholder")
        with self.assertRaises(Exception):
            doc.sufficientContext(concept, badContext)


    def test_set_separate_dimension_args(self):
        # Tests the case where .set() is called correctly.  Use the
        # way of calling .set() where we pass in every dimension
        # separately. Verify the data is stored and can be retrieved
        # using .get().
        doc = Entrypoint("CutSheet", self.taxonomy)

        # Write a TypeOfDevice and a DeviceCost:

        doc.set("solar:TypeOfDevice", "Module",
                duration="forever",
                ProductIdentifierAxis= "placeholder",
                TestConditionAxis = "placeholder",
                )
        doc.set("solar:DeviceCost", 100,
                instant= datetime.now(),
                ProductIdentifierAxis= "placeholder",
                TestConditionAxis= "placeholder",
                unit="dollars")

        self.assertEqual( doc.get("solar:TypeOfDevice", {}), "Module")
        self.assertEqual( doc.get("solar:DeviceCost", {}), 100)
        # TODO: DeviceCost should require units

    def test_set_context_arg(self):
        # Tests the case where .set() is called correctly, using
        # the way of calling .set() where we pass in a Context
        # object. Verify the data is stored and can be retrieved
        # using .get().
        doc = Entrypoint("CutSheet", self.taxonomy)
        ctx = Context(duration="forever",
                      entity="JUPITER",
                      ProductIdentifierAxis= "placeholder",
                      TestConditionAxis = "placeholder")
        doc.set("solar:TypeOfDevice", "Module", context=ctx)

        ctx = Context(instant= datetime.now(),
                      entity="JUPITER",
                      ProductIdentifierAxis= "placeholder",
                      TestConditionAxis = "placeholder")
        doc.set("solar:DeviceCost", 100, context=ctx, unit="dollars")



    def test_set_raises_exception(self):
        # Tests the case where .set() is called incorrectly. It should
        # raise exceptions if required information is missing.
        with self.assertRaises(Exception):
            doc.set("solar:TypeOfDevice", "Module", {})

        with self.assertRaises(Exception):
            doc.set("solar:DeviceCost", 100, {})
