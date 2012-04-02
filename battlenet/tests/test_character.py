# -*- coding: utf-8 -*-

import os
import battlenet
import datetime
from battlenet import Character

try:
    import unittest2 as unittest
except ImportError:
    import unittest as unittest

PUBLIC_KEY = os.environ.get('BNET_PUBLIC_KEY')
PRIVATE_KEY = os.environ.get('BNET_PRIVATE_KEY')

battlenet.Connection.setup(public_key=PUBLIC_KEY, private_key=PRIVATE_KEY)


class CharacterTest(unittest.TestCase):
    def test_general(self):
        character = Character(battlenet.UNITED_STATES, 'Nazjatar', 'Vishnevskiy')

        self.assertEqual(character.name, 'Vishnevskiy')
        self.assertEqual(str(character), 'Vishnevskiy')

        self.assertEqual(character.get_realm_name(), 'Nazjatar')
        self.assertEqual(character.realm.name, 'Nazjatar')
        self.assertEqual(str(character.realm), 'Nazjatar')

        self.assertEqual(character.faction, Character.HORDE)

        self.assertEqual(character.get_race_name(), Character.BLOOD_ELF)

        self.assertEqual(character.get_class_name(), Character.WARLOCK)

        self.assertIsInstance(character.level, int)
        self.assertGreaterEqual(character.level, 85)

        self.assertIsInstance(character.achievement_points, int)

        self.assertEqual(character.gender, Character.MALE)

    def test_guild(self):
        character = Character(battlenet.UNITED_STATES, 'Nazjatar', 'Vishnevskiy', fields=[Character.GUILD])

        self.assertEqual(character.guild.name, 'Excellence')

    def test_stats(self):
        character = Character(battlenet.UNITED_STATES, 'Nazjatar', 'Vishnevskiy', fields=[Character.STATS])

        self.assertIsInstance(character.stats.agility, int)

    def test_professions(self):
        character = Character(battlenet.UNITED_STATES, 'Nazjatar', 'Vishnevskiy', fields=[Character.PROFESSIONS])

        primary = character.professions['primary']

        tailoring = primary[0]
        enchanting = primary[1]

        self.assertEqual(tailoring.name, Character.TAILORING)
        self.assertIsInstance(tailoring.rank, int)
        self.assertIsInstance(tailoring.recipes, list)

        self.assertEqual(enchanting.name, Character.ENCHANTING)

        secondary = character.professions['secondary']

        first_aid = secondary[0]
        archaeology = secondary[1]

        self.assertEqual(first_aid.name, Character.FIRST_AID)
        self.assertEqual(archaeology.name, Character.ARCHAEOLOGY)

    def test_appearance(self):
        character = Character(battlenet.UNITED_STATES, 'Nazjatar', 'Vishnevskiy', fields=[Character.APPEARANCE])

        self.assertEqual(character.appearance.face, 0)
        self.assertEqual(character.appearance.feature, 9)
        self.assertEqual(character.appearance.hair_color, 4)
        self.assertEqual(character.appearance.show_cloak, False)
        self.assertEqual(character.appearance.show_helm, False)
        self.assertEqual(character.appearance.hair, 3)

    def test_lazyload(self):
        character = Character(battlenet.UNITED_STATES, 'Nazjatar', 'Vishnevskiy')

        self.assertEqual(character.guild.realm.name, 'Nazjatar')

    def test_unicode(self):
        character = Character(battlenet.UNITED_STATES, 'Nazjatar', 'Clí')

        self.assertEqual(character.name, 'Clí')

    def test_pet_class(self):
        character = Character(battlenet.UNITED_STATES, 'Nazjatar', 'Tandisse', fields=[Character.PETS])

        self.assertTrue(hasattr(character, 'pets'))
        self.assertIn('Rudebull', [pet.name for pet in character.pets])

    def test_achievements(self):
        character = Character(battlenet.UNITED_STATES, 'Nazjatar', 'Vishnevskiy', fields=[Character.ACHIEVEMENTS])

        self.assertEqual(character.achievements[513], datetime.datetime(2011, 1, 25, 12, 22, 8))

    def test_progression(self):
        character = Character(battlenet.UNITED_STATES, 'Nazjatar', 'Vishnevskiy', fields=[Character.PROGRESSION])

        for instance in character.progression['raids']:
            if instance.name == 'Blackwing Descent':
                self.assertTrue(instance.is_complete('normal'))

                for boss in instance.bosses:
                    if boss.name == 'Nefarian':
                        self.assertGreater(boss.normal, 0)

    def test_eu_character(self):
        character = Character(battlenet.EUROPE, 'Свежеватель Душ', 'Покерадуга')
        self.assertEqual(character.name, 'Покерадуга')

if __name__ == '__main__':
    unittest.main()
