# Copyright 2018 Wells Fargo

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
import taxonomy
import taxonomy_semantic
import taxonomy_types
import taxonomy_units
import taxonomy_misc


class TestTaxonomy(unittest.TestCase):

    def test_unit(self):
        self.assertIsInstance(taxonomy.Unit(), taxonomy.Unit)

    def test_element(self):
        self.assertIsInstance(taxonomy.Element(), taxonomy.Element)

    def test_taxonomy(self):
        tax = taxonomy.Taxonomy()
        self.assertIsInstance(tax, taxonomy.Taxonomy)
        self.assertIsInstance(tax.semantic, taxonomy_semantic.TaxonomySemantic)
        self.assertIsInstance(tax.types, taxonomy_types.TaxonomyTypes)
        self.assertIsInstance(tax.units, taxonomy_units.TaxonomyUnits)
        self.assertIsInstance(tax.misc, taxonomy_misc.TaxonomyMisc)
